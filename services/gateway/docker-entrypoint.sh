#!/usr/bin/env sh
# Entrypoint do Gateway:
#   1) aguarda o Postgres aceitar conexões;
#   2) aplica as migrations (alembic upgrade head) — idempotente;
#   3) sobe o uvicorn (chaves RSA de dev e seed de usuários acontecem no lifespan da app).
set -eu

MAX_WAIT="${DB_WAIT_SECONDS:-60}"
elapsed=0
until python - <<'PY' >/dev/null 2>&1
import sys
from sqlalchemy import create_engine, text
from app.core.config import get_settings
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
PY
do
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        echo "gateway: banco indisponível após ${MAX_WAIT}s, abortando" >&2
        exit 1
    fi
    echo "gateway: aguardando banco... (${elapsed}s)"
    sleep 2
    elapsed=$((elapsed + 2))
done

echo "gateway: aplicando migrations (alembic upgrade head)"
alembic upgrade head

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    "$@"
