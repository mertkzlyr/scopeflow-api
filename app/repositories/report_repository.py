from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


async def get_tasks_updated_in_period_for_projects(
    db: AsyncSession,
    project_ids: list[int],
    start_at: datetime,
    end_at: datetime,
) -> list[Task]:
    if not project_ids:
        return []

    result = await db.execute(
        select(Task)
        .where(
            Task.project_id.in_(project_ids),
            Task.updated_at >= start_at,
            Task.updated_at < end_at,
        )
        .order_by(Task.project_id, Task.id)
    )

    return list(result.scalars().all())