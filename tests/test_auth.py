from collections.abc import Generator
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app

def delete_user_by_email(email: str) -> None:
    database_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )

    with psycopg.connect(database_url) as connection:
        connection.execute("DELETE FROM users WHERE email = %s", (email,))
        connection.commit()


def unique_email() -> str:
    return f"test-{uuid4().hex}@example.com"


def register_test_user(client: TestClient, email: str, password: str = "password123"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
        },
    )


def test_register_user_success(client: TestClient):
    email = unique_email()

    try:
        response = register_test_user(client, email)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert "hashed_password" not in data
    finally:
        delete_user_by_email(email)


def test_register_user_duplicate_email_fails(client: TestClient):
    email = unique_email()

    try:
        first_response = register_test_user(client, email)
        second_response = register_test_user(client, email)

        assert first_response.status_code == 201
        assert second_response.status_code == 400
        assert second_response.json()["detail"] == "A user with this email already exists."
    finally:
        delete_user_by_email(email)


def test_login_success(client: TestClient):
    email = unique_email()

    try:
        register_response = register_test_user(client, email)
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )

        assert register_response.status_code == 201
        assert login_response.status_code == 200

        data = login_response.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]

        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["email"] == email
        assert payload["full_name"] == "Test User"
        assert payload["is_active"] is True
    finally:
        delete_user_by_email(email)


def test_login_invalid_password_fails(client: TestClient):
    email = unique_email()

    try:
        register_response = register_test_user(client, email)
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "wrong-password",
            },
        )

        assert register_response.status_code == 201
        assert login_response.status_code == 401
        assert login_response.json()["detail"] == "Incorrect email or password."
    finally:
        delete_user_by_email(email)


def test_get_current_user_success(client: TestClient):
    email = unique_email()

    try:
        register_response = register_test_user(client, email)
        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )
        token = login_response.json()["access_token"]

        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert register_response.status_code == 201
        assert login_response.status_code == 200
        assert me_response.status_code == 200

        data = me_response.json()
        assert data["email"] == email
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
    finally:
        delete_user_by_email(email)
