# ScopeFlow API — Agent Instructions

## Project Overview

ScopeFlow API is a production-style FastAPI backend for software agencies, freelancers, and small software teams.

The product focuses on:

- Client-approved task workflows
- Scope creep and change request tracking
- Multi-tenant SaaS organization structure
- Role-based access control
- Audit logs
- Weekly delivery reports

This is not a generic Trello/Jira clone. The goal is to build a realistic SaaS backend API that is understandable for a junior developer but designed with professional backend practices.

## Tech Stack

Use:

- Python 3.14
- uv for dependency and environment management
- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Alembic
- Pydantic / pydantic-settings
- JWT authentication
- Passlib / bcrypt
- Pytest
- Docker Compose

## Architecture Rules

Follow this layered architecture:

Router -> Service -> Repository -> Database

Responsibilities:

- Routers should only handle HTTP request/response logic.
- Services should contain business rules, authorization checks, workflow logic, and audit log coordination.
- Repositories should contain database queries only.
- SQLAlchemy models should only define database structure and relationships.
- Pydantic schemas should handle request and response validation.

Do not put raw SQLAlchemy queries inside routers unless it is a temporary health check.

## Current Project State

The project already has:

- uv project initialized
- FastAPI app in app/main.py
- health router in app/routers/health_router.py
- settings in app/core/config.py
- SQLAlchemy database connection in app/db/database.py
- Base model class in app/db/base.py
- PostgreSQL running via docker-compose.yml
- Alembic initialized and connected to app.db.base.Base.metadata

Continue from the next step: create the User model and the first Alembic migration.

## Coding Style

Keep the code beginner-friendly and explicit.

Prefer clear code over clever abstractions.

Use type hints where practical.

Avoid unnecessary generic base repository abstractions for now. Repositories can be simple classes or functions per entity.

Use async SQLAlchemy with AsyncSession, create_async_engine, async_sessionmaker, and asyncpg.

Use snake_case for Python files, functions, and variables.

Use PascalCase for SQLAlchemy models and Pydantic schemas.

## Database Conventions

Use integer primary keys for now.

Every main table should have:

- id
- created_at
- updated_at where appropriate

Use timezone-naive datetime with datetime.utcnow for now to keep the project simple.

Use PostgreSQL through SQLAlchemy.

All database schema changes must be created through Alembic migrations.

Migration files should be committed to git.

## Environment

Use uv commands.

Examples:

- Run app:
  uv run uvicorn app.main:app --reload

- Run Alembic:
  uv run alembic revision --autogenerate -m "message"
  uv run alembic upgrade head

- Run tests:
  uv run pytest

Do not use pip directly unless explicitly asked.

## Implementation Order

Follow this order unless instructed otherwise:

1. User model
2. Alembic migration for users table
3. Auth schemas
4. User repository
5. Security utilities for password hashing and JWT
6. Auth service
7. Auth router
8. Register endpoint
9. Login endpoint
10. /auth/me endpoint
11. Tests for auth

After auth works, continue with:

- organizations
- organization_members
- roles
- projects
- project_members
- tasks
- client approval workflow
- comments
- audit logs
- reports

## Important Business Rules

Eventually the app must support these roles:

- OWNER
- ADMIN
- MEMBER
- CLIENT
- VIEWER

Task statuses:

- TODO
- IN_PROGRESS
- IN_REVIEW
- CLIENT_REVIEW
- APPROVED
- REVISION_REQUESTED
- CANCELLED

Scope categories:

- ORIGINAL_SCOPE
- CHANGE_REQUEST
- BUG_FIX
- REVISION
- OUT_OF_SCOPE
- BILLABLE_EXTRA

Do not implement all of these at once. Build incrementally.

## Testing Expectations

When adding features, add or update tests when practical.

Use pytest.

Prefer readable test names such as:

- test_register_user_success
- test_register_user_duplicate_email_fails
- test_login_success
- test_login_invalid_password_fails
- test_get_current_user_success

## Safety Rules

Do not commit real secrets.

Do not remove .env from .gitignore.

Do not ignore uv.lock.

Do not delete existing working setup unless necessary.

Before making large changes, inspect the current files.
