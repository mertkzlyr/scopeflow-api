from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.repositories.organization_repository import (
    get_organization_by_id,
    get_organization_member,
)
from app.repositories.project_repository import (
    create_project,
    create_project_member,
    get_project_by_id,
    get_project_members,
    get_projects_for_organization,
)
from app.schemas.project import ProjectCreate


async def get_current_user_organization_membership(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
) -> OrganizationMember:
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

    return organization_member


async def create_project_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_data: ProjectCreate,
) -> Project:
    organization_member = await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
    ]

    if organization_member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create projects.",
        )

    project = await create_project(
        db=db,
        organization_id=organization_id,
        created_by_user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
    )

    await create_project_member(
        db=db,
        project_id=project.id,
        user_id=current_user.id,
    )

    await db.commit()
    await db.refresh(project)

    return project


async def list_projects_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
) -> list[Project]:
    await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    return await get_projects_for_organization(
        db=db,
        organization_id=organization_id,
    )


async def get_project_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
) -> Project:
    await get_current_user_organization_membership(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    project = await get_project_by_id(
        db=db,
        organization_id=organization_id,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


async def list_project_members_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    project_id: int,
) -> list[ProjectMember]:
    project = await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )

    return await get_project_members(
        db=db,
        project_id=project.id,
    )