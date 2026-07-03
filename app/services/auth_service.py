from jose import JWTError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from app.schemas.auth import Token, UserCreate, UserLogin


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    hashed_password = hash_password(user_data.password)

    return await create_user(
        db=db,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )


async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> User:
    user = await get_user_by_email(db, login_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    password_is_valid = verify_password(
        login_data.password,
        user.hashed_password,
    )
    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user.",
        )

    return user


async def login_user(db: AsyncSession, login_data: UserLogin) -> Token:
    user = await authenticate_user(db, login_data)
    access_token = create_access_token(subject=str(user.id))

    return Token(access_token=access_token)


async def get_current_user(db: AsyncSession, token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception

        user_id = int(subject)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user.",
        )

    return user
