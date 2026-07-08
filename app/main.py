from fastapi import FastAPI

from app.core.config import settings
from app.routers import (
    auth_router, 
    health_router, 
    organization_router, 
    project_router,
    task_router,
    comment_router,
    audit_log_router,
)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)


app.include_router(auth_router.router)
app.include_router(health_router.router)
app.include_router(organization_router.router)
app.include_router(project_router.router)
app.include_router(task_router.router)
app.include_router(comment_router.router)
app.include_router(audit_log_router.router)
