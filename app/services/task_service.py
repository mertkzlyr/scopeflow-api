from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import (
    create_task,
    get_task_by_id,
    get_tasks_for_project,
)
from app.schemas.task import TaskCreate
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