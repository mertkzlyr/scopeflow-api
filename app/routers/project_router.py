from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberResponse,
    ProjectResponse,
)
from app.services.auth_service import get_current_user
from app.services.project_service import (
    create_project_for_user,
    get_project_for_user,
    list_project_members_for_user,
    list_projects_for_user,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/projects",
    tags=["Projects"],
)

bearer_scheme = HTTPBearer()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    organization_id: int,
    project_data: ProjectCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await create_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_data=project_data,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    organization_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_projects_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    organization_id: int,
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await get_project_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )


@router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberResponse],
)
async def list_project_members(
    organization_id: int,
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_project_members_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )