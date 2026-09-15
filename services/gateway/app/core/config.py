from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "previo-pls-security"
    app_version: str = "1.0.0"

    # Prefixo público quando o Gateway roda atrás de um proxy que remove o
    # prefixo (nginx: /api/v1/* -> /v1/*). Afeta apenas /docs e /openapi.json.
    root_path: str = ""

    database_url: str = "postgresql+psycopg://previopls:previopls@localhost:5432/previopls"

    jwt_private_key_path: Path = Path("./keys/jwt_private.pem")
    jwt_public_key_path: Path = Path("./keys/jwt_public.pem")
    jwt_issuer: str = "previo-pls"
    jwt_audience: str = "previo-pls-clients"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    # Gera o par RSA automaticamente se os arquivos não existirem.
    # Default: apenas fora de produção (em prod as chaves vêm de KMS/Secret Files).
    jwt_auto_generate_keys: Optional[bool] = None

    fernet_key: str = Field(..., min_length=32)
    cpf_hash_pepper: str = Field(..., min_length=16)
    hmac_payload_secret: str = Field(..., min_length=16)

    # ---- Integração com o Core (Spring Boot) — ADR-001 / ADR-003 ----------
    # Quando CORE_API_URL está definido, /v1/clientes e /v1/leads* são
    # repassados ao Core com um JWT interno HS256 assinado com JWT_SECRET
    # (o mesmo segredo configurado no Core). Vazio = modo standalone
    # (o Gateway persiste o domínio no próprio banco, comportamento original).
    core_api_url: str = ""
    jwt_secret: str = ""
    core_timeout_seconds: float = 5.0
    core_internal_token_ttl_seconds: int = 60

    # Cria admin@ford.com / consultor@ford.com / analista@ford.com no boot.
    # Default: apenas fora de produção.
    seed_default_users: Optional[bool] = None

    # Primeiro administrador em produção (o Gateway não tem endpoint de gestão de
    # usuários). Com os dois definidos, o usuário é criado no boot se não existir;
    # a senha só é aplicada na criação. Para outros usuários: python -m app.db.seed --help
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""
    bootstrap_admin_name: str = "Administrador"

    cors_origins: str = ""
    rate_limit_global: str = "100/minute"
    rate_limit_login: str = "5/minute"
    rate_limit_llm: str = "10/minute"

    lockout_max_failures: int = 5
    lockout_window_seconds: int = 60
    lockout_duration_seconds: int = 900

    retention_years: int = 5

    security_alert_webhook_url: str = ""

    @field_validator("cors_origins")
    @classmethod
    def _validate_origins(cls, v: str) -> str:
        return v.strip()

    @field_validator("core_api_url", "root_path")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.strip().rstrip("/")

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        """Aceita a connection string como Neon/Render/Heroku entregam (postgres:// ou
        postgresql://) e converte para o dialeto do driver instalado (postgresql+psycopg://)."""
        v = v.strip()
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        if not self.cors_origins:
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    @property
    def core_proxy_enabled(self) -> bool:
        return bool(self.core_api_url)

    @property
    def should_seed_default_users(self) -> bool:
        if self.seed_default_users is None:
            return not self.is_prod
        return self.seed_default_users

    @property
    def should_auto_generate_keys(self) -> bool:
        if self.jwt_auto_generate_keys is None:
            return not self.is_prod
        return self.jwt_auto_generate_keys


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
