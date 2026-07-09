from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.enums.task_status import TaskStatus
from app.enums.scope_category import ScopeCategory
from app.models.task import Task
from app.models.user import User
from app.repositories.project_repository import get_project_member
from app.repositories.task_repository import (
    create_task,
    get_task_by_id,
    get_tasks_for_project,
    update_task_assignee,
    update_task_status,
    update_task
)
from app.repositories.user_repository import get_user_by_email
from app.schemas.task import TaskAssign, TaskCreate, TaskStatusUpdate, TaskUpdate
from app.services.project_service import (
    get_current_user_organization_membership,
    get_project_for_user,
)

from app.enums.audit_action import AuditAction
from app.services.audit_log_service import record_audit_log

async def create_task_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_data: TaskCreate,
) -> Task:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
        OrganizationRole.MEMBER,
    ]

    if organization_member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create tasks.",
        )

    await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    task = await create_task(
        db=db,
        project_id=project_id,
        created_by_user_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        scope_category=task_data.scope_category,
    )

    await record_audit_log(
        db=db,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        action=AuditAction.TASK_CREATED,
        entity_type="task",
        entity_id=task.id,
        metadata_json={
            "project_id": project_id,
            "task_title": task.title,
            "scope_category": task.scope_category.value,
        },
    )

    await db.commit()
    await db.refresh(task)

    return task


async def list_tasks_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    status_filter: TaskStatus | None = None,
    scope_category_filter: ScopeCategory | None = None,
    assigned_to_user_id_filter: int | None = None,
) -> list[Task]:
    await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    return await get_tasks_for_project(
        db=db,
        project_id=project_id,
        status=status_filter,
        scope_category=scope_category_filter,
        assigned_to_user_id=assigned_to_user_id_filter,
    )


async def get_task_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_id: int,
) -> Task:
    await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    task = await get_task_by_id(
        db=db,
        project_id=project_id,
        task_id=task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task

def build_task_update_audit_metadata(
    task: Task,
    update_data: dict[str, Any],
    project_id: int,
) -> dict[str, Any]:
    changes: dict[str, Any] = {}

    if "title" in update_data:
        changes["title"] = {
            "old": task.title,
            "new": update_data["title"],
        }

    if "description" in update_data:
        changes["description"] = {
            "old": task.description,
            "new": update_data["description"],
        }

    if "scope_category" in update_data:
        changes["scope_category"] = {
            "old": task.scope_category.value,
            "new": update_data["scope_category"].value,
        }

    return {
        "project_id": project_id,
        "changes": changes,
    }

async def update_task_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_id: int,
    task_data: TaskUpdate,
) -> Task:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
        OrganizationRole.MEMBER,
    ]

    if organization_member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update tasks.",
        )

    await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    task = await get_task_by_id(
        db=db,
        project_id=project_id,
        task_id=task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    update_data = task_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )

    audit_metadata = build_task_update_audit_metadata(
        task=task,
        update_data=update_data,
        project_id=project_id,
    )

    updated_task = await update_task(
        db=db,
        task=task,
        update_data=update_data,
    )

    await record_audit_log(
        db=db,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        action=AuditAction.TASK_UPDATED,
        entity_type="task",
        entity_id=task.id,
        metadata_json=audit_metadata,
    )

    await db.commit()
    await db.refresh(updated_task)

    return updated_task

async def update_task_status_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_id: int,
    status_data: TaskStatusUpdate,
) -> Task:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    task = await get_task_by_id(
        db=db,
        project_id=project_id,
        task_id=task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    validate_task_status_transition(
        current_status=task.status,
        new_status=status_data.status,
    )

    validate_task_status_permission(
        organization_role=organization_member.role,
        current_status=task.status,
        new_status=status_data.status,
    )

    old_status = task.status

    updated_task = await update_task_status(
        db=db,
        task=task,
        status=status_data.status,
        actor_user_id=current_user.id,
    )

    await record_audit_log(
        db=db,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        action=AuditAction.TASK_STATUS_CHANGED,
        entity_type="task",
        entity_id=task.id,
        metadata_json={
            "project_id": project_id,
            "old_status": old_status.value,
            "new_status": status_data.status.value,
        },
    )

    await db.commit()
    await db.refresh(updated_task)

    return updated_task

async def assign_task_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
    task_id: int,
    assign_data: TaskAssign,
) -> Task:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
        OrganizationRole.MEMBER,
    ]

    if organization_member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to assign tasks.",
        )

    await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    task = await get_task_by_id(
        db=db,
        project_id=project_id,
        task_id=task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    user_to_assign = await get_user_by_email(
        db=db,
        email=str(assign_data.email),
    )

    if user_to_assign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    project_member = await get_project_member(
        db=db,
        project_id=project_id,
        user_id=user_to_assign.id,
    )

    if project_member is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task can only be assigned to a project member.",
        )

    updated_task = await update_task_assignee(
        db=db,
        task=task,
        assigned_to_user_id=user_to_assign.id,
    )

    await record_audit_log(
        db=db,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        action=AuditAction.TASK_ASSIGNED,
        entity_type="task",
        entity_id=task.id,
        metadata_json={
            "project_id": project_id,
            "assigned_to_user_id": user_to_assign.id,
            "assigned_to_user_email": user_to_assign.email,
        },
    )

    await db.commit()
    await db.refresh(updated_task)

    return updated_task

def validate_task_status_transition(
    current_status: TaskStatus,
    new_status: TaskStatus,
) -> None:
    if current_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already has this status.",
        )

    allowed_transitions = {
        TaskStatus.TODO: [
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.IN_PROGRESS: [
            TaskStatus.IN_REVIEW,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.IN_REVIEW: [
            TaskStatus.CLIENT_REVIEW,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.CLIENT_REVIEW: [
            TaskStatus.APPROVED,
            TaskStatus.REVISION_REQUESTED,
        ],
        TaskStatus.REVISION_REQUESTED: [
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.APPROVED: [],
        TaskStatus.CANCELLED: [],
    }

    allowed_next_statuses = allowed_transitions[current_status]

    if new_status not in allowed_next_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task status transition.",
        )


def validate_task_status_permission(
    organization_role: OrganizationRole,
    current_status: TaskStatus,
    new_status: TaskStatus,
) -> None:
    is_client_review_decision = (
        current_status == TaskStatus.CLIENT_REVIEW
        and new_status
        in [
            TaskStatus.APPROVED,
            TaskStatus.REVISION_REQUESTED,
        ]
    )

    if is_client_review_decision:
        allowed_roles = [
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.CLIENT,
        ]
    else:
        allowed_roles = [
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.MEMBER,
        ]

    if organization_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this task status.",
        )
