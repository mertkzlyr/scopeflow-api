from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.scope_category import ScopeCategory
from app.enums.task_status import TaskStatus
from app.models.task import Task


async def create_task(
    db: AsyncSession,
    project_id: int,
    created_by_user_id: int,
    title: str,
    description: str | None,
    scope_category: ScopeCategory,
) -> Task:
    task = Task(
        project_id=project_id,
        created_by_user_id=created_by_user_id,
        title=title,
        description=description,
        status=TaskStatus.TODO,
        scope_category=scope_category,
    )

    db.add(task)
    await db.flush()

    return task


async def get_tasks_for_project(
    db: AsyncSession,
    project_id: int,
    status: TaskStatus | None = None,
    scope_category: ScopeCategory | None = None,
    assigned_to_user_id: int | None = None,
) -> list[Task]:
    statement = select(Task).where(Task.project_id == project_id)

    if status is not None:
        statement = statement.where(Task.status == status)

    if scope_category is not None:
        statement = statement.where(Task.scope_category == scope_category)

    if assigned_to_user_id is not None:
        statement = statement.where(
            Task.assigned_to_user_id == assigned_to_user_id
        )

    statement = statement.order_by(Task.id)

    result = await db.execute(statement)

    return list(result.scalars().all())


async def get_task_by_id(
    db: AsyncSession,
    project_id: int,
    task_id: int,
) -> Task | None:
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
        )
    )

    return result.scalar_one_or_none()

async def update_task_status(
    db: AsyncSession,
    task: Task,
    status: TaskStatus,
) -> Task:
    task.status = status

    await db.flush()

    return task

async def update_task_assignee(
    db: AsyncSession,
    task: Task,
    assigned_to_user_id: int,
) -> Task:
    task.assigned_to_user_id = assigned_to_user_id

    await db.flush()

    return task

async def update_task(
    db: AsyncSession,
    task: Task,
    update_data: dict[str, Any],
) -> Task:
    if "title" in update_data:
        task.title = update_data["title"]

    if "description" in update_data:
        task.description = update_data["description"]

    if "scope_category" in update_data:
        task.scope_category = update_data["scope_category"]

    await db.flush()

    return task