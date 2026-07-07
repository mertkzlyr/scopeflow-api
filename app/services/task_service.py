from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.enums.task_status import TaskStatus
from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import (
    create_task,
    get_task_by_id,
    get_tasks_for_project,
    update_task_status,
)
from app.schemas.task import TaskCreate, TaskStatusUpdate
from app.services.project_service import (
    get_current_user_organization_membership,
    get_project_for_user,
)


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

    await db.commit()
    await db.refresh(task)

    return task


async def list_tasks_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
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

    updated_task = await update_task_status(
        db=db,
        task=task,
        status=status_data.status,
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