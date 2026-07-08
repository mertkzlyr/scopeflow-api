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


def unique_task_title() -> str:
    return f"Test Task {uuid4().hex}"


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


def create_task(
    client: TestClient,
    token: str,
    organization_id: int,
    project_id: int,
    task_title: str,
) -> int:
    response = client.post(
        f"/organizations/{organization_id}/projects/{project_id}/tasks",
        json={
            "title": task_title,
            "description": None,
            "scope_category": "ORIGINAL_SCOPE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_owner_can_list_audit_logs(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()

    try:
        owner_token = register_and_login_user(client, owner_email)

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

        task_id = create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            task_title=task_title,
        )

        status_response = client.patch(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert status_response.status_code == 200

        response = client.get(
            f"/organizations/{organization_id}/audit-logs",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        actions = [log["action"] for log in data]

        assert "organization_created" in actions
        assert "project_created" in actions
        assert "task_created" in actions
        assert "task_status_changed" in actions

        task_status_log = next(
            log for log in data if log["action"] == "task_status_changed"
        )

        assert task_status_log["metadata"]["old_status"] == "TODO"
        assert task_status_log["metadata"]["new_status"] == "IN_PROGRESS"

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_member_cannot_list_audit_logs(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()
    organization_name = unique_organization_name()

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

        response = client.get(
            f"/organizations/{organization_id}/audit-logs",
            headers={"Authorization": f"Bearer {member_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to view audit logs."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)