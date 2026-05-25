-- Cria as duas bases isoladas para Core e Gateway.
-- Cada serviço aplica suas próprias migrations (Flyway no Core, Alembic no Gateway).
-- O usuário previopls é criado pelo entrypoint do postgres via POSTGRES_USER.

CREATE DATABASE previopls_core OWNER previopls;
CREATE DATABASE previopls_gateway OWNER previopls;

GRANT ALL PRIVILEGES ON DATABASE previopls_core TO previopls;
GRANT ALL PRIVILEGES ON DATABASE previopls_gateway TO previopls;
