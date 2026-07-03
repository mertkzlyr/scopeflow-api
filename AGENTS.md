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
- SQLAlchemy async support
- asyncpg
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

Do not put business logic inside routers.

## Async Rules

Use async consistently across the backend.

- Routers must use async def.
- Services must use async def.
- Repositories must use async def.
- Database access must use AsyncSession.
- Use create_async_engine.
- Use async_sessionmaker.
- Use asyncpg for application database access.
- Await database calls such as db.execute(), db.commit(), db.refresh(), and db.delete().
- Do not use synchronous SQLAlchemy Session in application code.
- Do not mix async FastAPI endpoints with synchronous SQLAlchemy database sessions.

The application DATABASE_URL should use this format:

postgresql+asyncpg://user:password@host:port/database

## Alembic Rules

The application uses async SQLAlchemy, but Alembic migrations may use the sync PostgreSQL driver.

If DATABASE_URL uses:

postgresql+asyncpg://...

then alembic/env.py should convert it to:

postgresql+psycopg://...

for migration execution.

Do not remove psycopg unless Alembic is fully converted to async migrations.

All database schema changes must be created through Alembic migrations.

Migration files should be committed to git.

## Current Project State

The project already has:

- uv project initialized
- FastAPI app in app/main.py
- health router in app/routers/health_router.py
- settings in app/core/config.py
- PostgreSQL running via docker-compose.yml
- async SQLAlchemy database connection in app/db/database.py
- Base model class in app/db/base.py
- Alembic initialized and connected to app.db.base.Base.metadata
- alembic/env.py imports app.models so autogenerate can discover models
- alembic/env.py converts postgresql+asyncpg:// to postgresql+psycopg:// for migration execution
- /health endpoint working
- /health/db endpoint working with AsyncSession
- User model in app/models/user.py
- users table migration created and applied
- Auth schemas in app/schemas/auth.py
- User repository in app/repositories/user_repository.py
- Security utilities for password hashing and JWT in app/core/security.py
- Auth service in app/services/auth_service.py
- Auth router in app/routers/auth_router.py
- /auth/register endpoint working
- /auth/login endpoint working
- /auth/me endpoint working with HTTP Bearer auth in Swagger
- JWT access tokens include sub, email, full_name, is_active, iat, and exp claims
- Auth tests in tests/test_auth.py passing

Continue from the next step: create the Organization and OrganizationMember models and the next Alembic migration.

## Coding Style

Keep the code beginner-friendly and explicit.

Prefer clear code over clever abstractions.

Use type hints where practical.

Avoid unnecessary generic base repository abstractions for now.

Use snake_case for Python files, functions, and variables.

Use PascalCase for SQLAlchemy models and Pydantic schemas.

Keep files small and focused.

## Database Conventions

Use integer primary keys for now.

Every main table should have:

- id
- created_at
- updated_at where appropriate

Use timezone-naive datetime with datetime.utcnow for now to keep the project simple.

Use PostgreSQL through SQLAlchemy.

## Environment and Commands

Use uv commands only.

Run app:

uv run uvicorn app.main:app --reload

Run Alembic:

uv run alembic revision --autogenerate -m "message"

uv run alembic upgrade head

Run tests:

uv run pytest

Do not use pip directly unless explicitly asked.

## Implementation Order

Build incrementally.

Next steps:

1. Organization model
2. OrganizationMember model
3. Role enum
4. Alembic migration for organizations and organization_members tables
5. Organization schemas
6. Organization repository
7. Organization service
8. Organization router
9. Organization endpoints

After organizations work, continue with:

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

## Git Rules

Do not commit real secrets.

Do not remove .env from .gitignore.

Do not ignore uv.lock.

Migration files should be committed.

Do not delete existing working setup unless necessary.

Before making large changes, inspect the current files.
