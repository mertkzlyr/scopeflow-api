from datetime import datetime, timedelta
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


def current_week_start() -> str:
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())

    return week_start.isoformat()


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
) -> None:
    response = client.post(
        f"/organizations/{organization_id}/projects/{project_id}/members",
        json={"email": email},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201


def create_task(
    client: TestClient,
    token: str,
    organization_id: int,
    project_id: int,
    task_title: str,
    scope_category: str = "ORIGINAL_SCOPE",
) -> int:
    response = client.post(
        f"/organizations/{organization_id}/projects/{project_id}/tasks",
        json={
            "title": task_title,
            "description": None,
            "scope_category": scope_category,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_owner_can_get_weekly_report(client: TestClient):
    owner_email = unique_email()
    organization_name = unique_organization_name()
    project_name = unique_project_name()
    approved_task_title = unique_task_title()
    change_request_task_title = unique_task_title()

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

        approved_task_id = create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            task_title=approved_task_title,
            scope_category="ORIGINAL_SCOPE",
        )

        create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=project_id,
            task_title=change_request_task_title,
            scope_category="CHANGE_REQUEST",
        )

        for next_status in [
            "IN_PROGRESS",
            "IN_REVIEW",
            "CLIENT_REVIEW",
            "APPROVED",
        ]:
            response = client.patch(
                f"/organizations/{organization_id}/projects/{project_id}/tasks/{approved_task_id}/status",
                json={"status": next_status},
                headers={"Authorization": f"Bearer {owner_token}"},
            )

            assert response.status_code == 200

        report_response = client.get(
            f"/organizations/{organization_id}/reports/weekly?week_start={current_week_start()}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert report_response.status_code == 200

        data = report_response.json()

        assert data["organization_id"] == organization_id
        assert data["total_tasks"] >= 2
        assert data["tasks_created"] >= 2
        assert data["approved_tasks"] >= 1
        assert data["change_request_tasks"] >= 1
        assert len(data["projects"]) >= 1

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)


def test_member_only_sees_assigned_project_in_weekly_report(client: TestClient):
    owner_email = unique_email()
    member_email = unique_email()

    organization_name = unique_organization_name()
    assigned_project_name = unique_project_name()
    unassigned_project_name = unique_project_name()

    assigned_task_title = unique_task_title()
    unassigned_task_title = unique_task_title()

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

        assigned_project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=assigned_project_name,
        )

        unassigned_project_id = create_project(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_name=unassigned_project_name,
        )

        add_project_member(
            client=client,
            owner_token=owner_token,
            organization_id=organization_id,
            project_id=assigned_project_id,
            email=member_email,
        )

        create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=assigned_project_id,
            task_title=assigned_task_title,
        )

        create_task(
            client=client,
            token=owner_token,
            organization_id=organization_id,
            project_id=unassigned_project_id,
            task_title=unassigned_task_title,
        )

        report_response = client.get(
            f"/organizations/{organization_id}/reports/weekly?week_start={current_week_start()}",
            headers={"Authorization": f"Bearer {member_token}"},
        )

        assert report_response.status_code == 200

        data = report_response.json()

        project_ids = [project["project_id"] for project in data["projects"]]

        assert assigned_project_id in project_ids
        assert unassigned_project_id not in project_ids

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(member_email)


def test_non_member_cannot_get_weekly_report(client: TestClient):
    owner_email = unique_email()
    outsider_email = unique_email()
    organization_name = unique_organization_name()

    try:
        owner_token = register_and_login_user(client, owner_email)
        outsider_token = register_and_login_user(client, outsider_email)

        organization_id = create_organization(
            client=client,
            token=owner_token,
            organization_name=organization_name,
        )

        response = client.get(
            f"/organizations/{organization_id}/reports/weekly?week_start={current_week_start()}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Organization not found."

    finally:
        delete_organization_by_name(organization_name)
        delete_user_by_email(owner_email)
        delete_user_by_email(outsider_email)