from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.repositories.organization_repository import (
    create_organization,
    create_organization_member,
    get_organization_by_id,
    get_organization_member,
    get_organization_members,
    get_organizations_for_user,
)
from app.repositories.user_repository import get_user_by_email
from app.schemas.organization import OrganizationCreate, OrganizationMemberCreate


async def create_organization_for_user(
    db: AsyncSession,
    current_user: User,
    organization_data: OrganizationCreate,
) -> Organization:
    organization = await create_organization(
        db=db,
        name=organization_data.name,
    )

    await create_organization_member(
        db=db,
        organization_id=organization.id,
        user_id=current_user.id,
        role=OrganizationRole.OWNER,
    )

    await db.commit()
    await db.refresh(organization)

    return organization


async def list_user_organizations(
    db: AsyncSession,
    current_user: User,
) -> list[Organization]:
    return await get_organizations_for_user(
        db=db,
        user_id=current_user.id,
    )


async def get_user_organization(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
) -> Organization:
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

    return organization


async def list_organization_members_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
) -> list[OrganizationMember]:
    await get_user_organization(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

    return await get_organization_members(
        db=db,
        organization_id=organization_id,
    )

async def add_organization_member_for_user(
    db: AsyncSession,
    current_user: User,
    organization_id: int,
    member_data: OrganizationMemberCreate,
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

    current_user_membership = await get_organization_member(
        db=db,
        organization_id=organization_id,
        user_id=current_user.id,
    )

    if current_user_membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    allowed_roles = [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
    ]

    if current_user_membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage organization members.",
        )

    if member_data.role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New members cannot be added as OWNER.",
        )

    user_to_add = await get_user_by_email(
        db=db,
        email=str(member_data.email),
    )

    if user_to_add is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    existing_membership = await get_organization_member(
        db=db,
        organization_id=organization_id,
        user_id=user_to_add.id,
    )

    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization.",
        )

    organization_member = await create_organization_member(
        db=db,
        organization_id=organization_id,
        user_id=user_to_add.id,
        role=member_data.role,
    )

    await db.commit()
    await db.refresh(organization_member)

    return organization_member