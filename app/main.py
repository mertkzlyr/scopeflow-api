from fastapi import FastAPI

from app.core.config import settings
from app.routers import health_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)


app.include_router(health_router.router)