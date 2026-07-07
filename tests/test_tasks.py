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


def test_create_task_success(client: TestClient):
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

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks",
            json={
                "title": task_title,
                "description": "Build the first task endpoint.",
                "scope_category": "ORIGINAL_SCOPE",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"]
        assert data["project_id"] == project_id
        assert data["created_by_user_id"]
        assert data["title"] == task_title
        assert data["description"] == "Build the first task endpoint."
        assert data["status"] == "TODO"
        assert data["scope_category"] == "ORIGINAL_SCOPE"
        assert "created_at" in data
        assert "updated_at" in data

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_list_tasks_success(client: TestClient):
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

        create_response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks",
            json={
                "title": task_title,
                "description": None,
                "scope_category": "BUG_FIX",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_response.status_code == 201

        list_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert list_response.status_code == 200

        data = list_response.json()

        assert len(data) >= 1
        assert any(task["title"] == task_title for task in data)

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_get_task_success(client: TestClient):
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

        create_response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks",
            json={
                "title": task_title,
                "description": "Task details.",
                "scope_category": "CHANGE_REQUEST",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_response.status_code == 201

        task_id = create_response.json()["id"]

        get_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert get_response.status_code == 200

        data = get_response.json()

        assert data["id"] == task_id
        assert data["title"] == task_title
        assert data["description"] == "Task details."
        assert data["status"] == "TODO"
        assert data["scope_category"] == "CHANGE_REQUEST"

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_client_role_cannot_create_task(client: TestClient):
    owner_email = unique_email()
    client_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()

    try:
        owner_token = register_and_login_user(client, owner_email)
        client_token = register_and_login_user(client, client_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=client_email,
            role="CLIENT",
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks",
            json={
                "title": task_title,
                "description": None,
                "scope_category": "ORIGINAL_SCOPE",
            },
            headers={"Authorization": f"Bearer {client_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to create tasks."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(client_email)


def test_non_member_cannot_list_tasks(client: TestClient):
    owner_email = unique_email()
    outsider_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        outsider_token = register_and_login_user(client, outsider_email)

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

        response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Organization not found."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(outsider_email)

def create_task(
    client: TestClient,
    token: str,
    organization_id: int,
    project_id: int,
    title: str,
    scope_category: str = "ORIGINAL_SCOPE",
) -> int:
    response = client.post(
        f"/organizations/{organization_id}/projects/{project_id}/tasks",
        json={
            "title": title,
            "description": None,
            "scope_category": scope_category,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()["id"]

def test_update_task_status_success(client: TestClient):
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
            title=task_title,
        )

        response = client.patch(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == task_id
        assert data["status"] == "IN_PROGRESS"

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_invalid_task_status_transition_fails(client: TestClient):
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
            title=task_title,
        )

        response = client.patch(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
            json={"status": "APPROVED"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid task status transition."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_client_can_approve_task_in_client_review(client: TestClient):
    owner_email = unique_email()
    client_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()

    try:
        owner_token = register_and_login_user(client, owner_email)
        client_token = register_and_login_user(client, client_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=client_email,
            role="CLIENT",
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
            title=task_title,
        )

        for next_status in [
            "IN_PROGRESS",
            "IN_REVIEW",
            "CLIENT_REVIEW",
        ]:
            response = client.patch(
                f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
                json={"status": next_status},
                headers={"Authorization": f"Bearer {owner_token}"},
            )

            assert response.status_code == 200

        approve_response = client.patch(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
            json={"status": "APPROVED"},
            headers={"Authorization": f"Bearer {client_token}"},
        )

        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "APPROVED"

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(client_email)


def test_member_cannot_approve_task_in_client_review(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()

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
            title=task_title,
        )

        for next_status in [
            "IN_PROGRESS",
            "IN_REVIEW",
            "CLIENT_REVIEW",
        ]:
            response = client.patch(
                f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
                json={"status": next_status},
                headers={"Authorization": f"Bearer {owner_token}"},
            )

            assert response.status_code == 200

        response = client.patch(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status",
            json={"status": "APPROVED"},
            headers={"Authorization": f"Bearer {member_token}"},
        )

        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You do not have permission to update this task status."
        )

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)