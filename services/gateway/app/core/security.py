"""
Camada de autenticação e autorização.

- JWT RS256 (assimétrica) com claims: sub, role, jti, iss, aud, iat, exp.
- access tokens curtos (15 min) + refresh tokens longos (7 dias) com rotação.
- Hash de senha via bcrypt (cost 12).
- Decorator/dependency requires_role para RBAC granular.
- JWT interno HS256 de curta duração para chamar o Core (ADR-003): o token
  externo RS256 nunca atravessa para a rede interna.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import lru_cache
from typing import Iterable

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db


log = get_logger(__name__)


class Role(str, Enum):
    CONSULTOR = "consultor"
    ADMIN = "admin"
    ANALISTA = "analista"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# ---- Carregamento das chaves RSA ------------------------------------------

def ensure_jwt_keys() -> bool:
    """
    Garante que o par RSA exista em disco.

    Fora de produção (ou com JWT_AUTO_GENERATE_KEYS=true) gera um par 2048 bits
    quando os arquivos não existem, para a stack subir sem passos manuais.
    Em produção as chaves devem vir de KMS / Secret Files; a ausência falha o boot.
    Retorna True se gerou chaves novas.
    """
    settings = get_settings()
    priv, pub = settings.jwt_private_key_path, settings.jwt_public_key_path
    if priv.exists() and pub.exists():
        return False
    if not settings.should_auto_generate_keys:
        raise RuntimeError(
            f"Chaves RSA do JWT não encontradas ({priv}, {pub}). "
            "Gere com scripts/gen_rsa_keys.sh ou monte via secret manager."
        )

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv.parent.mkdir(parents=True, exist_ok=True)
    pub.parent.mkdir(parents=True, exist_ok=True)
    priv.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    pub.write_bytes(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    try:
        priv.chmod(0o600)
    except OSError:
        pass
    _private_key.cache_clear()
    _public_key.cache_clear()
    log.warning("jwt.keys_generated", private=str(priv), public=str(pub),
                hint="chaves de desenvolvimento; em producao use KMS")
    return True


@lru_cache
def _private_key() -> bytes:
    return get_settings().jwt_private_key_path.read_bytes()


@lru_cache
def _public_key() -> bytes:
    return get_settings().jwt_public_key_path.read_bytes()


# ---- Senhas ---------------------------------------------------------------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ---- JWT ------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(*, subject: str, role: Role, nome: str | None = None) -> tuple[str, str]:
    """Retorna (token_assinado, jti)."""
    settings = get_settings()
    jti = uuid.uuid4().hex
    now = _now_utc()
    payload = {
        "sub": subject,
        "role": role.value,
        "nome": nome,
        "type": TokenType.ACCESS.value,
        "jti": jti,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_minutes)).timestamp()),
    }
    token = jwt.encode(payload, _private_key(), algorithm="RS256")
    return token, jti


def create_refresh_token(*, subject: str, role: Role) -> tuple[str, str, datetime]:
    """Retorna (token_assinado, jti, expira_em)."""
    settings = get_settings()
    jti = secrets.token_urlsafe(32)
    now = _now_utc()
    exp = now + timedelta(days=settings.jwt_refresh_ttl_days)
    payload = {
        "sub": subject,
        "role": role.value,
        "type": TokenType.REFRESH.value,
        "jti": jti,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, _private_key(), algorithm="RS256")
    return token, jti, exp


def decode_token(token: str, *, expected_type: TokenType) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            _public_key(),
            algorithms=["RS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "jti", "type"]},
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token expirado") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from e

    if payload.get("type") != expected_type.value:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido")

    return payload


# ---- HTTPBearer + dependências --------------------------------------------

class Principal:
    """Identidade autenticada propagada para handlers via Depends."""

    __slots__ = ("user_id", "role", "nome", "jti")

    def __init__(self, *, user_id: str, role: Role, nome: str | None, jti: str) -> None:
        self.user_id = user_id
        self.role = role
        self.nome = nome
        self.jti = jti


class _Bearer(HTTPBearer):
    """HTTPBearer que responde 401 + WWW-Authenticate (RFC 6750) em vez de 403."""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:  # type: ignore[override]
        try:
            creds = await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "UNAUTHORIZED", "message": "Não autenticado"},
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc
            raise
        if creds is None:  # pragma: no cover - auto_error=True nunca retorna None
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"code": "UNAUTHORIZED", "message": "Não autenticado"})
        return creds


_bearer = _Bearer(auto_error=True)


def current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Principal:
    payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    principal = Principal(
        user_id=payload["sub"],
        role=Role(payload["role"]),
        nome=payload.get("nome"),
        jti=payload["jti"],
    )
    # Propaga no request.state pra uso em middleware/audit
    request.state.principal = principal
    return principal


def requires_role(*allowed: Role):
    """
    Dependency factory para RBAC:

        @router.post("/x", dependencies=[Depends(requires_role(Role.ADMIN))])
    """
    allowed_set = set(allowed)

    def _checker(
        request: Request,
        principal: Principal = Depends(current_principal),
        db: Session = Depends(get_db),
    ) -> Principal:
        if principal.role not in allowed_set:
            # Trilha LGPD: tentativa de quebra de RBAC fica registrada (quem, onde, de onde).
            try:
                from app.models import AuditAction
                from app.services.audit_service import AuditService

                AuditService(db).log_event(
                    action=AuditAction.FORBIDDEN_ACCESS,
                    request=request,
                    details=f"{request.method} {request.url.path} requer {[r.value for r in allowed]}",
                )
                db.commit()
            except Exception:  # audit nunca derruba a resposta
                log.warning("audit.forbidden_failed", path=request.url.path)
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Acesso negado para o papel atual",
                    "required_roles": [r.value for r in allowed],
                },
            )
        return principal

    return _checker


# ---- JWT interno (Gateway -> Core, HS256) ---------------------------------

def create_internal_token(principal: Principal) -> str:
    """
    Emite o JWT interno HS256 aceito pelo Core (JwtService.parse).

    Claims: sub (id do usuário no Gateway), role, nome, iat, exp. TTL curto,
    um token por requisição. Assinado com JWT_SECRET, o mesmo segredo do Core.
    """
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET não configurado: necessário para chamar o Core")
    now = _now_utc()
    payload = {
        "sub": principal.user_id,
        "role": principal.role.value,
        "nome": principal.nome,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.core_internal_token_ttl_seconds)).timestamp()),
        "iss": settings.jwt_issuer,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
