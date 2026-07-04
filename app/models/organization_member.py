from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.organization_role import OrganizationRole


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    role = Column(
        SqlEnum(OrganizationRole, name="organization_role"),
        nullable=False,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = relationship(
        "Organization",
        back_populates="members",
    )
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_members_organization_id_user_id",
        ),
    )