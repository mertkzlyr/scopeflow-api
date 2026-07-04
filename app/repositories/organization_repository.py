from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.organization_role import OrganizationRole
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember


async def create_organization(
    db: AsyncSession,
    name: str,
) -> Organization:
    organization = Organization(name=name)

    db.add(organization)
    await db.flush()

    return organization


async def create_organization_member(
    db: AsyncSession,
    organization_id: int,
    user_id: int,
    role: OrganizationRole,
) -> OrganizationMember:
    organization_member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
    )

    db.add(organization_member)
    await db.flush()

    return organization_member


async def get_organization_by_id(
    db: AsyncSession,
    organization_id: int,
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )

    return result.scalar_one_or_none()


async def get_organization_member(
    db: AsyncSession,
    organization_id: int,
    user_id: int,
) -> OrganizationMember | None:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()


async def get_organizations_for_user(
    db: AsyncSession,
    user_id: int,
) -> list[Organization]:
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .order_by(Organization.id)
    )

    return list(result.scalars().all())


async def get_organization_members(
    db: AsyncSession,
    organization_id: int,
) -> list[OrganizationMember]:
    result = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == organization_id)
        .order_by(OrganizationMember.id)
    )

    return list(result.scalars().all())