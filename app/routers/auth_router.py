from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import get_current_user, login_user, register_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

bearer_scheme = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    return await register_user(db, user_data)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    return await login_user(db, login_data)


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    return await get_current_user(db, credentials.credentials)
