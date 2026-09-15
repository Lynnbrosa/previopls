"""
Login do Gateway sem banco (sessão fake):

- e-mail é normalizado (Admin@Ford.com autentica como admin@ford.com);
- tentativa falha e o evento LOGIN_FAILED são persistidos (commit) antes do 401, senão o
  rollback da sessão descartava tudo e o lockout nunca disparava;
- APP_ENV=prod também conta como produção.
"""
import os

from cryptography.fernet import Fernet

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("CPF_HASH_PEPPER", "test-pepper-32-bytes-padding-aaaaaaa")
os.environ.setdefault("HMAC_PAYLOAD_SECRET", "test-hmac-secret-32-bytes-padding-aaa")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://x:x@nohost/x")

from app.core.config import Settings, get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402

from app.core.errors import UnauthorizedError  # noqa: E402
from app.models import AuditLog, LoginAttempt  # noqa: E402
from app.schemas.auth import LoginRequest  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402


def test_login_request_lowercases_email():
    req = LoginRequest(email="  Admin@Ford.COM ", senha="admin123")
    assert req.email == "admin@ford.com"


@pytest.mark.parametrize("env,expected", [("production", True), ("prod", True), ("PRODUCTION ", True),
                                          ("development", False), ("staging", False), ("testing", False)])
def test_is_prod_variants(env, expected):
    s = Settings(app_env=env, fernet_key="x" * 44, cpf_hash_pepper="p" * 32, hmac_payload_secret="h" * 32)
    assert s.is_prod is expected


class _FakeSession:
    """scalar(): 0 para contagens (lockout), None para busca de usuário. Registra add/flush/commit."""

    def __init__(self):
        self.added = []
        self.commits = 0

    def scalar(self, stmt):
        return 0 if "count" in str(stmt).lower() else None

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        pass

    def commit(self):
        self.commits += 1


class _FakeRequest:
    class state:
        request_id = "req-1"
        principal = None

    class client:
        host = "203.0.113.9"

    headers = {"User-Agent": "pytest"}


def test_failed_login_is_persisted_before_401():
    db = _FakeSession()
    with pytest.raises(UnauthorizedError):
        AuthService(db).login("Nobody@Ford.com", "senha-errada", _FakeRequest())
    attempts = [o for o in db.added if isinstance(o, LoginAttempt)]
    audits = [o for o in db.added if isinstance(o, AuditLog)]
    assert len(attempts) == 1 and attempts[0].success is False and attempts[0].email == "nobody@ford.com"
    assert any(a.action.value == "LOGIN_FAILED" and a.actor_email == "nobody@ford.com" for a in audits)
    assert db.commits >= 1, "sem commit a tentativa falha é descartada no rollback e o lockout nunca dispara"


def test_forged_long_forwarded_ip_is_truncated_to_column_size():
    from app.services.audit_service import MAX_IP_LENGTH, client_ip

    class _Req:
        class state:
            request_id = "req-2"
            principal = None

        class client:
            host = "1" * 300  # X-Forwarded-For forjado chega como client.host via proxy headers

        headers = {"User-Agent": "pytest"}

    assert len(client_ip(_Req())) == MAX_IP_LENGTH
    assert client_ip(None) is None

    db = _FakeSession()
    with pytest.raises(UnauthorizedError):
        AuthService(db).login("nobody@ford.com", "senha-errada", _Req())
    attempt = next(o for o in db.added if isinstance(o, LoginAttempt))
    assert len(attempt.remote_ip) == MAX_IP_LENGTH


@pytest.mark.parametrize("raw,expected", [
    ("postgres://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
    ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("  postgresql+psycopg://u:p@host/db  ", "postgresql+psycopg://u:p@host/db"),
])
def test_database_url_is_normalized_to_psycopg_dialect(raw, expected):
    s = Settings(database_url=raw, fernet_key="x" * 44, cpf_hash_pepper="p" * 32, hmac_payload_secret="h" * 32)
    assert s.database_url == expected
