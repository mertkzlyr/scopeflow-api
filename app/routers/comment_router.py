from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.auth_service import get_current_user
from app.services.comment_service import (
    create_comment_for_user,
    list_comments_for_user,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"],
)

bearer_scheme = HTTPBearer()


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    organization_id: int,
    project_id: int,
    task_id: int,
    comment_data: CommentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await create_comment_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        comment_data=comment_data,
    )


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    organization_id: int,
    project_id: int,
    task_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_comments_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
    )