import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(180), nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    remote_ip = Column(String(64), nullable=True)
    attempted_at = Column(DateTime(timezone=True), default=_now, nullable=False, index=True)
