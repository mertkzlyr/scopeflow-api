from datetime import date

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.report import WeeklyReportResponse
from app.services.auth_service import get_current_user
from app.services.report_service import get_weekly_report_for_user

router = APIRouter(
    prefix="/organizations/{organization_id}/reports",
    tags=["Reports"],
)

bearer_scheme = HTTPBearer()


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    organization_id: int,
    week_start: date | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await get_weekly_report_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        week_start=week_start,
    )