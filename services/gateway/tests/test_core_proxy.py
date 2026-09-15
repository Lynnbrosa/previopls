"""
Testes do modo proxy Gateway -> Core (ADR-001 / ADR-003), sem banco e sem Core real:

- tradução do DTO snake_case para o contrato camelCase do Core;
- JWT interno HS256 verificável com o mesmo segredo do Core, papel preservado, TTL curto;
- indisponibilidade do Core vira 503 CORE_UNAVAILABLE;
- headers de correlação (X-Request-Id, X-Forwarded-For) propagados;
- geração automática do par RSA em ambiente de desenvolvimento.
"""
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import jwt
import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("CPF_HASH_PEPPER", "test-pepper-32-bytes-padding-aaaaaaa")
os.environ.setdefault("HMAC_PAYLOAD_SECRET", "test-hmac-secret-32-bytes-padding-aaa")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://x:x@nohost/x")
os.environ["CORE_API_URL"] = "http://core.test:5000"
os.environ["JWT_SECRET"] = "test-core-shared-secret-at-least-32-bytes-long"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.security import Principal, Role, create_internal_token, ensure_jwt_keys  # noqa: E402
from app.schemas.cliente import ClienteCreate  # noqa: E402
from app.services.core_client import CoreClient, CoreUnavailableError, to_core_payload  # noqa: E402


def _principal(role: Role = Role.ADMIN) -> Principal:
    return Principal(user_id="8b4f0d1e-1111-4222-8333-444455556666", role=role, nome="Admin Ford", jti="j1")


def _payload() -> ClienteCreate:
    return ClienteCreate.model_validate(
        {
            "nome": "Maria Silva",
            "cpf": "123.456.789-00",
            "email": "maria@example.com",
            "telefone": "+55 (11) 99999-8888",
            "regiao": "SP",
            "veiculo": {
                "modelo": "Ranger",
                "versao": "XLT",
                "ano": 2026,
                "vin": "9bfzzz8f7nb000001",
                "placa": "ABC1D23",
                "data_compra": "2026-05-13",
                "valor_compra": "250000.00",
                "concessionaria_id": "FORD-SP-001",
            },
        }
    )


def test_to_core_payload_translates_to_camel_case_and_drops_gateway_only_fields():
    body = to_core_payload(_payload())
    assert body["cpf"] == "12345678900"
    assert body["telefone"] == "+5511999998888"
    veiculo = body["veiculo"]
    assert veiculo["vin"] == "9BFZZZ8F7NB000001"
    assert veiculo["dataCompra"] == date(2026, 5, 13).isoformat()
    assert veiculo["valorCompra"] == str(Decimal("250000.00"))
    assert veiculo["concessionariaId"] == "FORD-SP-001"
    assert "placa" not in veiculo  # o Core não conhece placa
    assert "data_compra" not in veiculo


def test_internal_token_is_hs256_with_shared_secret_and_short_ttl():
    settings = get_settings()
    token = create_internal_token(_principal(Role.CONSULTOR))
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"require": ["exp", "iat", "sub"]})
    assert claims["sub"] == "8b4f0d1e-1111-4222-8333-444455556666"
    assert claims["role"] == "consultor"
    assert claims["exp"] - claims["iat"] == settings.core_internal_token_ttl_seconds


def test_internal_token_is_not_the_external_rs256_token():
    ensure_jwt_keys()
    from app.core.security import create_access_token

    external, _ = create_access_token(subject="u", role=Role.ADMIN)
    assert jwt.get_unverified_header(external)["alg"] == "RS256"
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(external, get_settings().jwt_secret, algorithms=["HS256"])


def test_forward_propagates_auth_and_correlation_headers():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["headers"] = request.headers
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"items": [], "page": 1, "perPage": 20, "total": 0})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://core.test:5000")

    class _State:
        request_id = "abc123"

    class _Client:
        host = "203.0.113.9"

    class _Req:
        state = _State()
        client = _Client()
        headers = {"User-Agent": "pytest"}

    resp = CoreClient(client).forward(
        "GET", "/v1/leads", principal=_principal(), request=_Req(), params={"status": "aberto", "prioridade": None, "page": 1}
    )
    assert resp.status_code == 200
    assert seen["headers"]["Authorization"].startswith("Bearer ")
    assert seen["headers"]["X-Request-Id"] == "abc123"
    assert seen["headers"]["X-Forwarded-For"] == "203.0.113.9"
    assert "prioridade" not in seen["url"] and "status=aberto" in seen["url"]


def test_forward_maps_connection_error_to_503():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://core.test:5000")
    with pytest.raises(CoreUnavailableError) as excinfo:
        CoreClient(client).forward("GET", "/v1/leads", principal=_principal())
    assert excinfo.value.status_code == 503
    assert excinfo.value.code == "CORE_UNAVAILABLE"


def test_forward_passes_upstream_errors_through():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"error": {"code": "CONFLICT", "message": "Cliente já cadastrado"}})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://core.test:5000")
    resp = CoreClient(client).forward("POST", "/v1/clientes", principal=_principal(), json={})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_ensure_jwt_keys_generates_dev_pair(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    priv, pub = tmp_path / "k" / "priv.pem", tmp_path / "k" / "pub.pem"
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_private_key_path", priv)
    monkeypatch.setattr(settings, "jwt_public_key_path", pub)
    monkeypatch.setattr(settings, "jwt_auto_generate_keys", True)
    assert ensure_jwt_keys() is True
    assert priv.read_bytes().startswith(b"-----BEGIN PRIVATE KEY-----")
    assert pub.read_bytes().startswith(b"-----BEGIN PUBLIC KEY-----")
    assert ensure_jwt_keys() is False  # idempotente


def test_ensure_jwt_keys_refuses_to_generate_when_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_private_key_path", tmp_path / "missing_priv.pem")
    monkeypatch.setattr(settings, "jwt_public_key_path", tmp_path / "missing_pub.pem")
    monkeypatch.setattr(settings, "jwt_auto_generate_keys", False)
    with pytest.raises(RuntimeError):
        ensure_jwt_keys()
