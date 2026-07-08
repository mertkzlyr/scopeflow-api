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

def add_project_member(
    client: TestClient,
    owner_token: str,
    organization_id: int,
    project_id: int,
    email: str,
) -> int:
    response = client.post(
        f"/organizations/{organization_id}/projects/{project_id}/members",
        json={"email": email},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201

    return response.json()["user_id"]


def create_task(
    client: TestClient,
    token: str,
    organization_id: int,
    project_id: int,
    title: str,
) -> int:
    response = client.post(
        f"/organizations/{organization_id}/projects/{project_id}/tasks",
        json={
            "title": title,
            "description": None,
            "scope_category": "ORIGINAL_SCOPE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_create_comment_success(client: TestClient):
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

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            json={"body": "This is the first comment."},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"]
        assert data["task_id"] == task_id
        assert data["author_user_id"]
        assert data["body"] == "This is the first comment."
        assert "created_at" in data
        assert "updated_at" in data

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_list_comments_success(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()
    comment_body = "Please clarify the acceptance criteria."

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

        create_response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            json={"body": comment_body},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_response.status_code == 201

        list_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert list_response.status_code == 200

        data = list_response.json()

        assert len(data) >= 1
        assert any(comment["body"] == comment_body for comment in data)

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_client_can_create_comment(client: TestClient):
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

        add_project_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            email=client_email,
        )

        task_id = create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            title=task_title,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            json={"body": "Client requested a revision."},
            headers={"Authorization": f"Bearer {client_token}"},
        )

        assert response.status_code == 201
        assert response.json()["body"] == "Client requested a revision."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(client_email)


def test_viewer_cannot_create_comment(client: TestClient):
    owner_email = unique_email()
    viewer_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()

    try:
        owner_token = register_and_login_user(client, owner_email)
        viewer_token = register_and_login_user(client, viewer_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=viewer_email,
            role="VIEWER",
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        add_project_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            email=viewer_email,
        )

        task_id = create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            title=task_title,
        )

        response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            json={"body": "Viewer should not be able to comment."},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to create comments."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(viewer_email)


def test_viewer_can_list_comments(client: TestClient):
    owner_email = unique_email()
    viewer_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    task_title = unique_task_title()
    comment_body = "Visible to viewer."

    try:
        owner_token = register_and_login_user(client, owner_email)
        viewer_token = register_and_login_user(client, viewer_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        add_organization_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            email=viewer_email,
            role="VIEWER",
        )

        project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=project_name,
        )

        add_project_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            email=viewer_email,
        )

        task_id = create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            title=task_title,
        )

        create_comment_response = client.post(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            json={"body": comment_body},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_comment_response.status_code == 201

        list_response = client.get(
            f"/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert list_response.status_code == 200

        data = list_response.json()

        assert any(comment["body"] == comment_body for comment in data)

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(viewer_email)