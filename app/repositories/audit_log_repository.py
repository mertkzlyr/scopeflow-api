from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.audit_action import AuditAction
from app.models.audit_log import AuditLog


async def create_audit_log(
    db: AsyncSession,
    organization_id: int,
    actor_user_id: int | None,
    action: AuditAction,
    entity_type: str,
    entity_id: int,
    metadata_json: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata_json,
    )

    db.add(audit_log)
    await db.flush()

    return audit_log


async def get_audit_logs_for_organization(
    db: AsyncSession,
    organization_id: int,
    limit: int = 100,
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
    )

    return list(result.scalars().all())