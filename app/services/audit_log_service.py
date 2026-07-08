from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.audit_action import AuditAction
from app.enums.organization_role import OrganizationRole
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import (
    create_audit_log,
    get_audit_logs_for_organization,
)
from app.repositories.organization_repository import (
    get_organization_by_id,
    get_organization_member,
)


async def record_audit_log(
    db: AsyncSession,
    organization_id: int,
    actor_user_id: int | None,
    action: AuditAction,
    entity_type: str,
    entity_id: int,
    metadata_json: dict[str, Any] | None = None,
) -> AuditLog:
    return await create_audit_log(
        db=db,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata_json,
    )


async def list_audit_logs_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
) -> list[AuditLog]:
    organization = await get_organization_by_id(
        db=db,
        organization_id=organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    organization_member = await get_organization_member(
        db=db,
        organization_id=organization_id,
        user_id=current_user.id,
    )

    if organization_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
    ]

    if organization_member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view audit logs.",
        )

    return await get_audit_logs_for_organization(
        db=db,
        organization_id=organization_id,
    )