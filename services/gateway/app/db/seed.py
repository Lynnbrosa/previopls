"""
Seed de usuários padrão para desenvolvimento e demo.

Espelha o DataSeeder do Core (admin@ford.com / consultor@ford.com) e adiciona
o papel analista, exclusivo do Gateway. Idempotente: só cria quem não existe.
Ativado por SEED_DEFAULT_USERS (default: fora de produção).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import RolePapel, Usuario


log = get_logger(__name__)

DEFAULT_USERS = (
    ("Admin Ford", "admin@ford.com", "admin123", RolePapel.ADMIN),
    ("Carlos Consultor", "consultor@ford.com", "cons123", RolePapel.CONSULTOR),
    ("Ana Analista", "analista@ford.com", "analista123", RolePapel.ANALISTA),
)


def seed_default_users(db: Session) -> int:
    created = 0
    for nome, email, senha, papel in DEFAULT_USERS:
        exists = db.scalar(select(Usuario.id).where(Usuario.email == email))
        if exists is not None:
            continue
        db.add(Usuario(nome=nome, email=email, senha_hash=hash_password(senha), papel=papel))
        created += 1
        log.info("seed.user_created", email=email, papel=papel.value)
    if created:
        db.commit()
    return created
