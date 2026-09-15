from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1 import api_v1
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.core.ratelimit import limiter
from app.core.security import ensure_jwt_keys
from app.db.session import SessionLocal, engine


configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Chaves RSA: em dev são geradas se não existirem; em prod a ausência falha o boot.
    ensure_jwt_keys()

    # Usuários: primeiro admin de produção (BOOTSTRAP_ADMIN_*) e, fora de produção, os de demo.
    # As migrations já rodaram no entrypoint (alembic upgrade head).
    from app.db.seed import bootstrap_admin, seed_default_users

    try:
        with SessionLocal() as db:
            created_admin = bootstrap_admin(db)
            created = seed_default_users(db) if settings.should_seed_default_users else 0
        log.info("seed.done", bootstrap_admin=created_admin, demo_users_created=created,
                 demo_seed_enabled=settings.should_seed_default_users)
    except Exception as exc:  # não derruba a API: /health vai reportar o banco
        log.error("seed.failed", error=str(exc))

    log.info(
        "app.started",
        env=settings.app_env,
        version=settings.app_version,
        core_proxy=settings.core_proxy_enabled,
        core_api_url=settings.core_api_url or None,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PrevioPLS Security API",
        version=settings.app_version,
        description=(
            "Borda de segurança LGPD do PrevioPLS: TLS (nginx), JWT RS256, HMAC nos webhooks, "
            "rate limit, RBAC e trilha de auditoria. Com CORE_API_URL configurado, as operações "
            "de domínio (/v1/clientes, /v1/leads) são repassadas ao Core com JWT interno HS256."
        ),
        root_path=settings.root_path,
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not settings.is_prod else None,
        lifespan=lifespan,
    )

    # Middlewares (ordem importa: o último registrado é o mais externo).
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-Signature", "X-Timestamp"],
        expose_headers=["X-Request-Id"],
        max_age=3600,
    )
    app.add_middleware(RequestIdMiddleware)

    # Rate limit (slowapi anexa state ao app + exception handler)
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Limite excedido: {exc.detail}",
                }
            },
            headers={"Retry-After": "60"},
        )

    register_exception_handlers(app)

    app.include_router(api_v1)

    @app.get("/health", tags=["meta"])
    def health():
        components: dict[str, str] = {}
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            components["database"] = "up"
        except Exception:
            components["database"] = "down"
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "components": components},
            )

        if settings.core_proxy_enabled:
            from app.services.core_client import CoreClient

            components["core"] = "up" if CoreClient().health() else "down"

        degraded = any(v != "up" for v in components.values())
        return {"status": "degraded" if degraded else "ok", "components": components}

    @app.get("/version", tags=["meta"])
    def version():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "mode": "core-proxy" if settings.core_proxy_enabled else "standalone",
            "build_time": datetime.now(timezone.utc).isoformat(),
        }

    return app


app = create_app()
