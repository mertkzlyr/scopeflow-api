from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log_service import list_audit_logs_for_user
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/organizations/{organization_id}/audit-logs",
    tags=["Audit Logs"],
)

bearer_scheme = HTTPBearer()


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    organization_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user(db, credentials.credentials)

    return await list_audit_logs_for_user(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
    )