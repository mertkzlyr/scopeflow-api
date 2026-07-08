from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import (
    create_comment,
    get_comments_for_task,
)
from app.schemas.comment import CommentCreate
from app.services.project_service import get_current_user_organization_membership
from app.services.task_service import get_task_for_user

from app.enums.audit_action import AuditAction
from app.services.audit_log_service import record_audit_log

async def create_comment_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_id: int,
    comment_data: CommentCreate,
) -> Comment:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
        OrganizationRole.MEMBER,
        OrganizationRole.CLIENT,
    ]

    if organization_member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create comments.",
        )

    task = await get_task_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
    )

    comment = await create_comment(
        db=db,
        task_id=task.id,
        author_user_id=current_user.id,
        body=comment_data.body,
    )

    await record_audit_log(
    db=db,
    organization_id=organization_id,
    actor_user_id=current_user.id,
    action=AuditAction.COMMENT_CREATED,
    entity_type="comment",
    entity_id=comment.id,
    metadata_json={
        "project_id": project_id,
        "task_id": task.id,
    },
)

    await db.commit()
    await db.refresh(comment)

    return comment


async def list_comments_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_id: int,
) -> list[Comment]:
    task = await get_task_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
    )

    return await get_comments_for_task(
        db=db,
        task_id=task.id,
    )