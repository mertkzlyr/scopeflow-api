from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.enums.scope_category import ScopeCategory
from app.enums.task_status import TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    assigned_to_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    revision_requested_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_at = Column(DateTime, nullable=True)
    revision_requested_at = Column(DateTime, nullable=True)

    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        SqlEnum(TaskStatus, name="task_status"),
        default=TaskStatus.TODO,
        nullable=False,
    )

    scope_category = Column(
        SqlEnum(ScopeCategory, name="scope_category"),
        default=ScopeCategory.ORIGINAL_SCOPE,
        nullable=False,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")

    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )

    assigned_to_user = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
    )

    comments = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    approved_by_user = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )

    revision_requested_by_user = relationship(
        "User",
        foreign_keys=[revision_requested_by_user_id],
    )