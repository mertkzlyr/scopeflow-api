from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from app.core.config import settings


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


def unique_project_name() -> str:
    return f"Test Project {uuid4().hex}"


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


def create_organization(
    client: TestClient,
    token: str,
    organization_name: str,
) -> int:
    response = client.post(
        "/organizations",
        json={"name": organization_name},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()["id"]

def create_project(
    client: TestClient,
    token: str,
    organization_id: int,
    project_name: str,
) -> int:
    response = client.post(
        f"/organizations/{organization_id}/projects",
        json={
            "name": project_name,
            "description": None,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()["id"]


def add_organization_member(
    client: TestClient,
    owner_token: str,
    organization_id: int,
    email: str,
    role: str,
) -> None:
    response = client.post(
        f"/organizations/{organization_id}/members",
        json={
            "email": email,
            "role": role,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201


def test_create_project_success(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects",
            json={
                "name": project_name,
                "description": "A test project.",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"]
        assert data["organization_id"] == organization_id
        assert data["name"] == project_name
        assert data["description"] == "A test project."
        assert "created_at" in data
        assert "updated_at" in data

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_list_projects_success(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        create_response = client.post(
            f"/organizations/{organization_id}/projects",
            json={
                "name": project_name,
                "description": None,
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_response.status_code == 201

        list_response = client.get(
            f"/organizations/{organization_id}/projects",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert list_response.status_code == 200

        data = list_response.json()

        assert len(data) >= 1
        assert any(project["name"] == project_name for project in data)

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_get_project_success(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        create_response = client.post(
            f"/organizations/{organization_id}/projects",
            json={
                "name": project_name,
                "description": "Project details.",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_response.status_code == 201

        project_id = create_response.json()["id"]

        get_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert get_response.status_code == 200

        data = get_response.json()

        assert data["id"] == project_id
        assert data["name"] == project_name
        assert data["description"] == "Project details."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_member_cannot_create_project(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        member_token = register_and_login_user(client, member_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=member_email,
            role="MEMBER",
        )

        response = client.post(
            f"/organizations/{organization_id}/projects",
            json={
                "name": project_name,
                "description": None,
            },
            headers={"Authorization": f"Bearer {member_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to create projects."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)


def test_list_project_members_success(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        create_project_response = client.post(
            f"/organizations/{organization_id}/projects",
            json={
                "name": project_name,
                "description": None,
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_project_response.status_code == 201

        project_id = create_project_response.json()["id"]

        members_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert members_response.status_code == 200

        data = members_response.json()

        assert len(data) == 1
        assert data[0]["project_id"] == project_id

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)

def test_add_project_member_success(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        register_and_login_user(client, member_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=member_email,
            role="MEMBER",
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            json={"email": member_email},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["project_id"] == project_id
        assert data["user_id"]

        members_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert members_response.status_code == 200

        members = members_response.json()

        assert len(members) == 2

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)


def test_add_project_member_requires_organization_membership(client: TestClient):
    owner_email = unique_email()
    outsider_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        register_and_login_user(client, outsider_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            json={"email": outsider_email},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "User must be an organization member before being added to a project."
        )

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(outsider_email)


def test_add_project_member_duplicate_fails(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        register_and_login_user(client, member_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=member_email,
            role="MEMBER",
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        first_response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            json={"email": member_email},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        second_response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            json={"email": member_email},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 400
        assert (
            second_response.json()["detail"]
            == "User is already a member of this project."
        )

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)


def test_regular_member_cannot_add_project_member(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()
    third_user_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        member_token = register_and_login_user(client, member_email)
        register_and_login_user(client, third_user_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=member_email,
            role="MEMBER",
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=third_user_email,
            role="MEMBER",
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/members",
            json={"email": third_user_email},
            headers={"Authorization": f"Bearer {member_token}"},
        )

        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You do not have permission to manage project members."
        )

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)
        delete_user_by_email(third_user_email)