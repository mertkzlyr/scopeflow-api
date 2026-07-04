from collections.abc import Generator
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

def get_sync_database_url() -> str:
    return settings.DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )


def delete_user_by_email(email: str) -> None:
    with psycopg.connect(get_sync_database_url()) as connection:
        connection.execute("DELETE FROM users WHERE email = %s", (email,))
        connection.commit()


def delete_organization_by_name(name: str) -> None:
    with psycopg.connect(get_sync_database_url()) as connection:
        connection.execute(
            "DELETE FROM organizations WHERE name = %s",
            (name,),
        )
        connection.commit()


def unique_email() -> str:
    return f"test-{uuid4().hex}@example.com"


def unique_organization_name() -> str:
    return f"Test Organization {uuid4().hex}"


def register_and_login_user(
    client: TestClient,
    email: str,
    password: str = "password123",
) -> str:
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_create_organization_success(client: TestClient):
    email = unique_email()
    organization_name = unique_organization_name()

    try:
        token = register_and_login_user(client, email)

        response = client.post(
            "/organizations",
            json={"name": organization_name},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"]
        assert data["name"] == organization_name
        assert "created_at" in data
        assert "updated_at" in data

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(email)


def test_list_organizations_success(client: TestClient):
    email = unique_email()
    organization_name = unique_organization_name()

    try:
        token = register_and_login_user(client, email)

        create_response = client.post(
            "/organizations",
            json={"name": organization_name},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_response.status_code == 201

        list_response = client.get(
            "/organizations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200

        data = list_response.json()

        assert len(data) >= 1
        assert any(
            organization["name"] == organization_name
            for organization in data
        )

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(email)


def test_get_organization_success(client: TestClient):
    email = unique_email()
    organization_name = unique_organization_name()

    try:
        token = register_and_login_user(client, email)

        create_response = client.post(
            "/organizations",
            json={"name": organization_name},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_response.status_code == 201

        organization_id = create_response.json()["id"]

        get_response = client.get(
            f"/organizations/{organization_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert get_response.status_code == 200

        data = get_response.json()

        assert data["id"] == organization_id
        assert data["name"] == organization_name

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(email)


def test_get_organization_not_member_returns_404(client: TestClient):
    owner_email = unique_email()
    other_email = unique_email()
    organization_name = unique_organization_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        other_token = register_and_login_user(client, other_email)

        create_response = client.post(
            "/organizations",
            json={"name": organization_name},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_response.status_code == 201

        organization_id = create_response.json()["id"]

        get_response = client.get(
            f"/organizations/{organization_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert get_response.status_code == 404
        assert get_response.json()["detail"] == "Organization not found."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(other_email)


def test_list_organization_members_success(client: TestClient):
    email = unique_email()
    organization_name = unique_organization_name()

    try:
        token = register_and_login_user(client, email)

        create_response = client.post(
            "/organizations",
            json={"name": organization_name},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_response.status_code == 201

        organization_id = create_response.json()["id"]

        members_response = client.get(
            f"/organizations/{organization_id}/members",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert members_response.status_code == 200

        data = members_response.json()

        assert len(data) == 1
        assert data[0]["organization_id"] == organization_id
        assert data[0]["role"] == "OWNER"

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(email)