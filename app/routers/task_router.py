from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.task import TaskCreate, TaskResponse, TaskStatusUpdate, TaskAssign
from app.services.auth_service import get_current_user
from app.services.task_service import (
    create_task_for_user,
    get_task_for_user,
    list_tasks_for_user,
    update_task_status_for_user,
    assign_task_for_user
)

router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/tasks",
    tags=["Tasks"],
)

bearer_scheme = HTTPBearer()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    organization_id: int,
    project_id: int,
    task_data: TaskCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await create_task_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_data=task_data,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    organization_id: int,
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_tasks_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    organization_id: int,
    project_id: int,
    task_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await get_task_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
    )

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    organization_id: int,
    project_id: int,
    task_id: int,
    status_data: TaskStatusUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await update_task_status_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        status_data=status_data,
    )

@router.patch("/{task_id}/assignee", response_model=TaskResponse)
async def assign_task(
    organization_id: int,
    project_id: int,
    task_id: int,
    assign_data: TaskAssign,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await assign_task_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        assign_data=assign_data,
    )