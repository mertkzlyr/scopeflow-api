from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


async def create_comment(
    db: AsyncSession,
    task_id: int,
    author_user_id: int,
    body: str,
) -> Comment:
    comment = Comment(
        task_id=task_id,
        author_user_id=author_user_id,
        body=body,
    )

    db.add(comment)
    await db.flush()

    return comment


async def get_comments_for_task(
    db: AsyncSession,
    task_id: int,
) -> list[Comment]:
    result = await db.execute(
        select(Comment)
        .where(Comment.task_id == task_id)
        .order_by(Comment.id)
    )

    return list(result.scalars().all())