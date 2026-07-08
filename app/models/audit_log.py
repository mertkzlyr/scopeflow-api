from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.audit_action import AuditAction


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    action = Column(
        SqlEnum(AuditAction, name="audit_action"),
        index=True,
        nullable=False,
    )

    entity_type = Column(String, index=True, nullable=False)
    entity_id = Column(Integer, index=True, nullable=False)

    metadata_json = Column("metadata", JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization")
    actor_user = relationship("User")