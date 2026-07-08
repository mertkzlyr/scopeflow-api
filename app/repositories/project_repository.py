from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember


async def create_project(
    db: AsyncSession,
    organization_id: int,
    created_by_user_id: int,
    name: str,
    description: str | None,
) -> Project:
    project = Project(
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        name=name,
        description=description,
    )

    db.add(project)
    await db.flush()

    return project


async def create_project_member(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> ProjectMember:
    project_member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
    )

    db.add(project_member)
    await db.flush()

    return project_member


async def get_projects_for_organization(
    db: AsyncSession,
    organization_id: int,
) -> list[Project]:
    result = await db.execute(
        select(Project)
        .where(Project.organization_id == organization_id)
        .order_by(Project.id)
    )

    return list(result.scalars().all())


async def get_project_by_id(
    db: AsyncSession,
    organization_id: int,
    project_id: int,
) -> Project | None:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
    )

    return result.scalar_one_or_none()


async def get_project_member(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()


async def get_project_members(
    db: AsyncSession,
    project_id: int,
) -> list[ProjectMember]:
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.id)
    )

    return list(result.scalars().all())

async def get_projects_for_user_in_organization(
    db: AsyncSession,
    organization_id: int,
    user_id: int,
) -> list[Project]:
    result = await db.execute(
        select(Project)
        .join(ProjectMember)
        .where(
            Project.organization_id == organization_id,
            ProjectMember.user_id == user_id,
        )
        .order_by(Project.id)
    )

    return list(result.scalars().all())