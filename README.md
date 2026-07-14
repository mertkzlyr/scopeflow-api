# ScopeFlow API

ScopeFlow API is a production-style FastAPI backend for software agencies, freelancers, and small teams that need to manage client-approved task workflows, scope creep, change requests, project access, audit history, and weekly delivery reports.

The project is built around a multi-tenant SaaS structure where users belong to organizations, organizations contain projects, and projects contain tasks, comments, members, approval workflows, and reportable activity.

## Features

* JWT-based authentication
* User registration, login, and current-user endpoint
* Multi-tenant organization structure
* Organization roles:

  * `OWNER`
  * `ADMIN`
  * `MEMBER`
  * `CLIENT`
  * `VIEWER`
* Organization members
* Projects under organizations
* Project-level access control
* Project members
* Task management
* Task assignment
* Task status workflow
* Client approval workflow
* Scope category tracking
* Task comments
* Audit logs
* Weekly reports
* Async SQLAlchemy database layer
* Alembic migrations
* PostgreSQL with Docker Compose
* Pytest test suite

## Tech Stack

* Python 3.14+
* FastAPI
* SQLAlchemy ORM async
* asyncpg
* PostgreSQL
* Alembic
* Pydantic / pydantic-settings
* JWT authentication
* Passlib / bcrypt
* Pytest
* Docker Compose
* uv

## Architecture

The project follows a layered backend architecture:

```text
Router -> Service -> Repository -> Database
```

Responsibilities are separated as follows:

```text
Routers:
- HTTP endpoints
- Request/response handling
- Dependency injection

Services:
- Business logic
- Authorization checks
- Workflow rules
- Transaction boundaries

Repositories:
- Database queries
- SQLAlchemy ORM operations

Models:
- Database tables
- Relationships
- SQLAlchemy mappings

Schemas:
- Request and response validation
- Pydantic models
```

Business logic is intentionally kept in the service layer instead of routers or repositories.

## Project Structure

```text
scopeflow-api/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── base.py
│   │   └── database.py
│   ├── enums/
│   ├── models/
│   ├── repositories/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

## Core Domain

ScopeFlow is designed around this workflow:

```text
User registers
-> User creates an organization
-> User becomes organization OWNER
-> OWNER adds organization members
-> OWNER / ADMIN creates projects
-> Project members are added
-> Tasks are created inside projects
-> Tasks move through a controlled status workflow
-> Clients approve or request revisions
-> Comments and audit logs preserve context
-> Weekly reports summarize delivery and scope changes
```

## Roles

Organization roles define what a user can do inside an organization.

| Role     | Description                                                    |
| -------- | -------------------------------------------------------------- |
| `OWNER`  | Full organization control                                      |
| `ADMIN`  | Can manage projects, members, and tasks                        |
| `MEMBER` | Can work on assigned projects and tasks                        |
| `CLIENT` | Can review tasks, approve work, request revisions, and comment |
| `VIEWER` | Read-only project visibility when assigned                     |

Project-level access control is enforced separately from organization membership.

`OWNER` and `ADMIN` can access all projects in an organization.

`MEMBER`, `CLIENT`, and `VIEWER` can only access projects where they are explicitly added as project members.

## Task Status Workflow

Tasks move through the following statuses:

```text
TODO
-> IN_PROGRESS
-> IN_REVIEW
-> CLIENT_REVIEW
-> APPROVED
```

Clients can approve work or request changes from `CLIENT_REVIEW`:

```text
CLIENT_REVIEW -> APPROVED
CLIENT_REVIEW -> REVISION_REQUESTED
REVISION_REQUESTED -> IN_PROGRESS
```

Tasks can also be cancelled from supported active states.

Available task statuses:

```text
TODO
IN_PROGRESS
IN_REVIEW
CLIENT_REVIEW
APPROVED
REVISION_REQUESTED
CANCELLED
```

## Scope Categories

Each task has a scope category so teams can track original work, revisions, bugs, scope creep, and billable extras.

Available scope categories:

```text
ORIGINAL_SCOPE
CHANGE_REQUEST
BUG_FIX
REVISION
OUT_OF_SCOPE
BILLABLE_EXTRA
```

## API Overview

### Health

```http
GET /health
GET /health/db
```

### Auth

```http
POST /auth/register
POST /auth/login
GET /auth/me
```

### Organizations

```http
POST /organizations
GET /organizations
GET /organizations/{organization_id}
GET /organizations/{organization_id}/members
POST /organizations/{organization_id}/members
```

### Projects

```http
POST /organizations/{organization_id}/projects
GET /organizations/{organization_id}/projects
GET /organizations/{organization_id}/projects/{project_id}
GET /organizations/{organization_id}/projects/{project_id}/members
POST /organizations/{organization_id}/projects/{project_id}/members
```

### Tasks

```http
POST /organizations/{organization_id}/projects/{project_id}/tasks
GET /organizations/{organization_id}/projects/{project_id}/tasks
GET /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}
PATCH /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}
PATCH /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status
PATCH /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/assignee
```

Task list supports filters:

```http
GET /organizations/{organization_id}/projects/{project_id}/tasks?status=IN_PROGRESS
GET /organizations/{organization_id}/projects/{project_id}/tasks?scope_category=CHANGE_REQUEST
GET /organizations/{organization_id}/projects/{project_id}/tasks?assigned_to_user_id=1
```

### Comments

```http
POST /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments
GET /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments
```

### Audit Logs

```http
GET /organizations/{organization_id}/audit-logs
```

Audit logs track important actions such as:

```text
ORGANIZATION_CREATED
ORGANIZATION_MEMBER_ADDED
PROJECT_CREATED
PROJECT_MEMBER_ADDED
TASK_CREATED
TASK_UPDATED
TASK_ASSIGNED
TASK_STATUS_CHANGED
COMMENT_CREATED
```

### Reports

```http
GET /organizations/{organization_id}/reports/weekly
GET /organizations/{organization_id}/reports/weekly?week_start=2026-07-06
```

Weekly reports include organization-level and project-level summaries for:

```text
total_tasks
tasks_created
approved_tasks
revision_requested_tasks
change_request_tasks
out_of_scope_tasks
billable_extra_tasks
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/mertkzlyr/scopeflow-api.git
cd scopeflow-api
```

### 2. Create environment file

```bash
cp .env.example .env
```

Default development values:

```env
PROJECT_NAME=ScopeFlow API
ENVIRONMENT=development
JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

POSTGRES_USER=scopeflow_user
POSTGRES_PASSWORD=scopeflow_password
POSTGRES_DB=scopeflow_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://scopeflow_user:scopeflow_password@localhost:5432/scopeflow_db
```

For real deployments, replace `JWT_SECRET_KEY` with a strong secret value.

### 3. Start PostgreSQL

```bash
docker compose up -d
```

### 4. Install dependencies

```bash
uv sync
```

### 5. Run migrations

```bash
uv run alembic upgrade head
```

### 6. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API docs:

```text
http://localhost:8000/docs
```

## Running Tests

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=app
```

## Database Migrations

Create a new migration:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Check current migration:

```bash
uv run alembic current
```

Check migration history:

```bash
uv run alembic history
```

## Development Notes

The application uses async SQLAlchemy for runtime database access:

```text
postgresql+asyncpg://...
```

Alembic migrations use a sync PostgreSQL driver internally. The Alembic environment converts the async database URL to a sync-compatible URL for migrations.

Use `uv` for all Python commands in this project.

Recommended commands:

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run alembic upgrade head
uv run pytest
```

## Example Workflow

### 1. Register a user

```http
POST /auth/register
```

```json
{
  "email": "owner@example.com",
  "full_name": "Owner User",
  "password": "password123"
}
```

### 2. Login

```http
POST /auth/login
```

```json
{
  "email": "owner@example.com",
  "password": "password123"
}
```

### 3. Create an organization

```http
POST /organizations
```

```json
{
  "name": "Acme Agency"
}
```

The creator automatically becomes the organization `OWNER`.

### 4. Add a client to the organization

```http
POST /organizations/{organization_id}/members
```

```json
{
  "email": "client@example.com",
  "role": "CLIENT"
}
```

### 5. Create a project

```http
POST /organizations/{organization_id}/projects
```

```json
{
  "name": "Website Redesign",
  "description": "Client website redesign project"
}
```

### 6. Add the client to the project

```http
POST /organizations/{organization_id}/projects/{project_id}/members
```

```json
{
  "email": "client@example.com"
}
```

### 7. Create a task

```http
POST /organizations/{organization_id}/projects/{project_id}/tasks
```

```json
{
  "title": "Update homepage hero section",
  "description": "Revise hero copy and CTA layout.",
  "scope_category": "ORIGINAL_SCOPE"
}
```

### 8. Move task through review

```http
PATCH /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status
```

```json
{
  "status": "IN_PROGRESS"
}
```

```json
{
  "status": "IN_REVIEW"
}
```

```json
{
  "status": "CLIENT_REVIEW"
}
```

### 9. Client approves the task

```http
PATCH /organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/status
```

```json
{
  "status": "APPROVED"
}
```

When a task is approved, the API stores:

```text
approved_at
approved_by_user_id
```

When a client requests revisions, the API stores:

```text
revision_requested_at
revision_requested_by_user_id
```

## Security and Access Control

The API uses JWT bearer authentication.

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

Access control is enforced at both organization and project levels.

Important rules:

```text
Only organization members can access organization resources.
OWNER and ADMIN can manage organization/project resources.
MEMBER can work on assigned projects.
CLIENT can review tasks and comment on assigned projects.
VIEWER has read-only access to assigned projects.
Project existence is hidden from unauthorized users.
```

## Testing Strategy

The test suite covers:

```text
Authentication
Organization creation and membership
Project creation and membership
Project-level access control
Task creation and listing
Task updates
Task assignment
Task status transitions
Client approval details
Comments
Audit logs
Weekly reports
Authorization failures
```

Tests use unique generated data and clean up records after execution.

## Current Status

ScopeFlow API currently includes the core backend features needed for a portfolio-ready SaaS-style backend:

```text
Auth
Organizations
Roles
Projects
Project members
Tasks
Task workflow
Client approval
Comments
Audit logs
Weekly reports
Tests
Migrations
```

## Future Improvements

Potential next improvements:

```text
Pagination
Search
Refresh tokens
Email invitations
Organization update/delete endpoints
Project update/archive endpoints
Task archive/delete endpoints
Rate limiting
CI workflow
Deployment configuration
Dockerfile for API service
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
