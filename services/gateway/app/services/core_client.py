"""
Cliente HTTP do Gateway para o Core (Spring Boot) — ADR-001 / ADR-003.

O Gateway valida borda (TLS, JWT RS256, HMAC, schema, rate limit, audit) e
repassa as operações de domínio ao Core na rede interna. Cada chamada leva:

- Authorization: Bearer <JWT interno HS256>, emitido por requisição com o papel
  do principal autenticado no Gateway (o token externo nunca atravessa);
- X-Request-Id: o mesmo correlation id do Gateway, para casar os dois audit logs;
- X-Forwarded-For: IP do cliente original, para o audit do Core registrar a origem.

Respostas do Core (2xx ou erro no formato {error:{code,message,details}}) são
devolvidas ao cliente como estão. Falhas de rede/timeout viram 503 CORE_UNAVAILABLE.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping, Optional

import httpx
from fastapi import Request, Response, status

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.security import Principal, create_internal_token
from app.schemas.cliente import ClienteCreate


log = get_logger(__name__)


class CoreUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "CORE_UNAVAILABLE"


@lru_cache
def _http_client() -> httpx.Client:
    settings = get_settings()
    return httpx.Client(
        base_url=settings.core_api_url,
        timeout=httpx.Timeout(settings.core_timeout_seconds, connect=2.0),
        headers={"Accept": "application/json"},
    )


def to_core_payload(payload: ClienteCreate) -> dict[str, Any]:
    """Traduz o DTO snake_case do Gateway para o contrato camelCase do Core."""
    v = payload.veiculo
    return {
        "nome": payload.nome,
        "cpf": payload.cpf,
        "email": payload.email,
        "telefone": payload.telefone,
        "regiao": payload.regiao,
        "veiculo": {
            "modelo": v.modelo,
            "versao": v.versao,
            "ano": v.ano,
            "vin": v.vin,
            "dataCompra": v.data_compra.isoformat(),
            "valorCompra": str(v.valor_compra),
            "concessionariaId": v.concessionaria_id,
        },
    }


class CoreClient:
    def __init__(self, client: Optional[httpx.Client] = None) -> None:
        self._client = client or _http_client()

    def forward(
        self,
        method: str,
        path: str,
        *,
        principal: Principal,
        request: Optional[Request] = None,
        json: Any = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {create_internal_token(principal)}"}
        if request is not None:
            request_id = getattr(request.state, "request_id", None)
            if request_id:
                headers["X-Request-Id"] = request_id
            if request.client and request.client.host:
                headers["X-Forwarded-For"] = request.client.host
            ua = request.headers.get("User-Agent")
            if ua:
                headers["User-Agent"] = ua[:255]

        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        try:
            response = self._client.request(method, path, json=json, params=clean_params, headers=headers)
        except httpx.HTTPError as exc:
            log.error("core.unavailable", method=method, path=path, error=type(exc).__name__)
            raise CoreUnavailableError(
                "Serviço de domínio indisponível. Tente novamente em instantes.",
                details={"upstream": "core"},
            ) from exc

        log.info("core.forwarded", method=method, path=path, status_code=response.status_code)
        return response

    def health(self) -> bool:
        try:
            r = self._client.get("/health", timeout=2.0)
            return r.status_code == 200
        except httpx.HTTPError:
            return False


def passthrough(response: httpx.Response) -> Response:
    """Devolve a resposta do Core ao cliente sem re-serializar (mesmo status e corpo)."""
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )
