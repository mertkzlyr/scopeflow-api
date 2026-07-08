from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.enums.audit_action import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    organization_id: int
    actor_user_id: int | None
    action: AuditAction
    entity_type: str
    entity_id: int
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )