"""
Criação de usuários do Gateway.

O Gateway não expõe endpoint de gestão de usuários (superfície de ataque menor);
usuários entram por três caminhos, todos idempotentes:

1. seed_default_users(): admin/consultor/analista de demonstração. Espelha o
   DataSeeder do Core. Ativado por SEED_DEFAULT_USERS (default: fora de produção).
2. bootstrap_admin(): primeiro administrador em produção, via BOOTSTRAP_ADMIN_EMAIL
   e BOOTSTRAP_ADMIN_PASSWORD. Criado no boot se não existir; a senha só vale na criação.
3. CLI: python -m app.db.seed --email x@ford.com --papel consultor [--nome ...] [--senha ...]
   Sem --senha, lê de GATEWAY_USER_PASSWORD ou pede no terminal. Use no shell do container.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import RolePapel, Usuario


log = get_logger(__name__)

DEFAULT_USERS = (
    ("Admin Ford", "admin@ford.com", "admin123", RolePapel.ADMIN),
    ("Carlos Consultor", "consultor@ford.com", "cons123", RolePapel.CONSULTOR),
    ("Ana Analista", "analista@ford.com", "analista123", RolePapel.ANALISTA),
)

MIN_PASSWORD_LENGTH = 6  # mesmo mínimo do LoginRequest


def ensure_user(db: Session, *, nome: str, email: str, senha: str, papel: RolePapel) -> bool:
    """Cria o usuário se o email ainda não existe. Retorna True se criou."""
    email = email.strip().lower()
    if len(senha) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"senha precisa de pelo menos {MIN_PASSWORD_LENGTH} caracteres")
    exists = db.scalar(select(Usuario.id).where(Usuario.email == email))
    if exists is not None:
        return False
    db.add(Usuario(nome=nome.strip() or email, email=email, senha_hash=hash_password(senha), papel=papel))
    db.commit()
    log.info("seed.user_created", email=email, papel=papel.value)
    return True


def seed_default_users(db: Session) -> int:
    created = 0
    for nome, email, senha, papel in DEFAULT_USERS:
        if ensure_user(db, nome=nome, email=email, senha=senha, papel=papel):
            created += 1
    return created


def bootstrap_admin(db: Session) -> bool:
    """Garante o primeiro admin a partir de BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD."""
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return False
    return ensure_user(
        db,
        nome=settings.bootstrap_admin_name,
        email=settings.bootstrap_admin_email,
        senha=settings.bootstrap_admin_password,
        papel=RolePapel.ADMIN,
    )


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.db.seed",
        description="Cria um usuário do Gateway (idempotente por email).",
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--papel", required=True, choices=[r.value for r in RolePapel])
    parser.add_argument("--nome", default="")
    parser.add_argument("--senha", default=None, help="omitido: usa GATEWAY_USER_PASSWORD ou pede no terminal")
    args = parser.parse_args(argv)

    senha = args.senha or os.environ.get("GATEWAY_USER_PASSWORD") or getpass.getpass("Senha: ")

    from app.db.session import SessionLocal

    with SessionLocal() as db:
        created = ensure_user(db, nome=args.nome, email=args.email, senha=senha, papel=RolePapel(args.papel))
    print(f"{'criado' if created else 'já existia'}: {args.email.strip().lower()} ({args.papel})")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
