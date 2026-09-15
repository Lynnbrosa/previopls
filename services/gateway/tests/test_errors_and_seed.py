"""
- Rotas desconhecidas seguem o contrato {error:{code,message}} (404 vinha como {"detail": "Not Found"}).
- Bootstrap do primeiro admin e seed são idempotentes e validam a senha (sem banco: sessão fake).
"""
import os

from cryptography.fernet import Fernet

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("CPF_HASH_PEPPER", "test-pepper-32-bytes-padding-aaaaaaa")
os.environ.setdefault("HMAC_PAYLOAD_SECRET", "test-hmac-secret-32-bytes-padding-aaa")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://x:x@nohost/x")

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.seed import DEFAULT_USERS, bootstrap_admin, ensure_user, seed_default_users  # noqa: E402
from app.models import RolePapel  # noqa: E402


def _client():
    from app.main import app

    # Sem "with": não executa o lifespan (nem banco, nem chaves).
    return TestClient(app)


def test_unknown_route_uses_error_contract():
    r = _client().get("/rota-que-nao-existe")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "NOT_FOUND", "message": "Not Found"}}


def test_method_not_allowed_uses_error_contract():
    r = _client().delete("/health")
    assert r.status_code == 405
    assert r.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


class _FakeSession:
    """Simula a sessão apenas para o que o seed usa: scalar(select) por email, add e commit."""

    def __init__(self, existing=()):
        self.emails = set(existing)
        self.added = []
        self.commits = 0

    def scalar(self, stmt):
        # extrai o literal comparado em `Usuario.email == <valor>`
        email = stmt.whereclause.right.value
        return object() if email in self.emails else None

    def add(self, obj):
        self.added.append(obj)
        self.emails.add(obj.email)

    def commit(self):
        self.commits += 1


def test_ensure_user_is_idempotent_and_normalizes_email():
    db = _FakeSession()
    assert ensure_user(db, nome="Gestor", email="  Gestor@Ford.com ", senha="segredo1", papel=RolePapel.ADMIN) is True
    assert ensure_user(db, nome="Gestor", email="gestor@ford.com", senha="outra-senha", papel=RolePapel.ADMIN) is False
    assert len(db.added) == 1
    user = db.added[0]
    assert user.email == "gestor@ford.com"
    assert user.papel is RolePapel.ADMIN
    assert user.senha_hash.startswith("$2b$12$")  # bcrypt cost 12, nunca a senha em claro


def test_ensure_user_rejects_short_password():
    with pytest.raises(ValueError):
        ensure_user(_FakeSession(), nome="x", email="x@ford.com", senha="123", papel=RolePapel.CONSULTOR)


def test_seed_default_users_creates_only_missing():
    db = _FakeSession(existing={"admin@ford.com"})
    assert seed_default_users(db) == len(DEFAULT_USERS) - 1
    assert seed_default_users(db) == 0


def test_bootstrap_admin_noop_without_env(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "bootstrap_admin_email", "")
    monkeypatch.setattr(settings, "bootstrap_admin_password", "")
    assert bootstrap_admin(_FakeSession()) is False


def test_bootstrap_admin_creates_first_admin(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "bootstrap_admin_email", "gestor@ford.com")
    monkeypatch.setattr(settings, "bootstrap_admin_password", "senha-forte-1")
    monkeypatch.setattr(settings, "bootstrap_admin_name", "Gestor")
    db = _FakeSession()
    assert bootstrap_admin(db) is True
    assert db.added[0].papel is RolePapel.ADMIN
    assert bootstrap_admin(db) is False  # segunda vez: já existe
