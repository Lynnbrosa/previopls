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

import threading
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


class CoreAuthMismatchError(AppError):
    """O Core rejeitou o JWT interno que o próprio Gateway assinou: JWT_SECRET divergente."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "CORE_AUTH_MISMATCH"


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

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            # O token interno é emitido aqui mesmo, então um 401 do Core nunca é "sessão expirada"
            # do usuário: é configuração (JWT_SECRET diferente entre gateway e core). Repassar o
            # 401 fazia o painel derrubar a sessão em loop; 502 aponta para a causa real.
            log.error("core.auth_mismatch", method=method, path=path, upstream_status=401)
            raise CoreAuthMismatchError(
                "O Core rejeitou o token interno do Gateway. Confira se JWT_SECRET é o mesmo no gateway e no core "
                "(ou se os relógios dos dois serviços estão dessincronizados).",
                details={"upstream": "core", "upstream_status": 401},
            )

        log.info("core.forwarded", method=method, path=path, status_code=response.status_code)
        return response

    def health(self) -> bool:
        try:
            r = self._client.get("/health", timeout=2.0)
            return r.status_code == 200
        except httpx.HTTPError:
            return False


_warmup_lock = threading.Lock()
_warmup_running = False


def warm_up_core(
    client: Optional[httpx.Client] = None,
    timeout_seconds: Optional[float] = None,
) -> Optional[threading.Thread]:
    """
    Acorda o Core em segundo plano (fire-and-forget), sem segurar a requisição atual.

    Em free tier (Render) o Core suspende após inatividade e leva 1 a 2 min para voltar; a
    primeira leitura do painel cairia em 503 CORE_UNAVAILABLE. Disparar um GET /health no boot
    do Gateway e a cada login faz o Core começar a subir enquanto o painel ainda navega.
    Só um aquecimento roda por vez. Devolve a thread iniciada, ou None quando não há o que
    fazer (modo standalone, CORE_WARMUP_SECONDS=0 ou aquecimento já em andamento).
    """
    global _warmup_running
    settings = get_settings()
    timeout = settings.core_warmup_seconds if timeout_seconds is None else timeout_seconds
    if timeout <= 0 or (client is None and not settings.core_proxy_enabled):
        return None
    with _warmup_lock:
        if _warmup_running:
            return None
        _warmup_running = True

    http = client or _http_client()

    def _run() -> None:
        global _warmup_running
        try:
            r = http.get("/health", timeout=httpx.Timeout(timeout, connect=10.0))
            log.info("core.warmup", status_code=r.status_code)
        except httpx.HTTPError as exc:
            log.warning("core.warmup_failed", error=type(exc).__name__)
        except Exception as exc:  # nunca deixa a thread morrer com traceback cru no stderr
            log.warning("core.warmup_failed", error=type(exc).__name__, unexpected=True)
        finally:
            with _warmup_lock:
                _warmup_running = False

    thread = threading.Thread(target=_run, name="core-warmup", daemon=True)
    try:
        thread.start()
    except Exception as exc:
        # Sem thread disponível: libera a flag e segue. O login já foi confirmado no banco e
        # não pode virar 500 por causa do aquecimento.
        with _warmup_lock:
            _warmup_running = False
        log.warning("core.warmup_failed", error=type(exc).__name__, stage="start")
        return None
    return thread


def passthrough(response: httpx.Response) -> Response:
    """Devolve a resposta do Core ao cliente sem re-serializar (mesmo status e corpo)."""
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )
