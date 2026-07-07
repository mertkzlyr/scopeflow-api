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
) -> list[Task]:
    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.id)
    )

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
