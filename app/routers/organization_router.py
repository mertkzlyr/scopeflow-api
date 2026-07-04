from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationMemberCreate,
)
from app.services.auth_service import get_current_user
from app.services.organization_service import (
    create_organization_for_user,
    get_user_organization,
    list_organization_members_for_user,
    list_user_organizations,
    add_organization_member_for_user,
)

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)

bearer_scheme = HTTPBearer()


@router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    organization_data: OrganizationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await create_organization_for_user(
        db=db,
        current_user=current_user,
        organization_data=organization_data,
    )


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_user_organizations(
        db=db,
        current_user=current_user,
    )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await get_user_organization(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )


@router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
)
async def list_organization_members(
    organization_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_organization_members_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )

@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=201,
)
async def add_organization_member(
    organization_id: int,
    member_data: OrganizationMemberCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await add_organization_member_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        member_data=member_data,
    )