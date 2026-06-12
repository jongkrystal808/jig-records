from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth import require_permission
from backend.app.core.database import get_db
from backend.app.schemas.audit import AuditLogRead
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_permission("read"))])


@router.get("/logs", response_model=list[AuditLogRead])
def list_audit_logs(
    customer_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return AuditService(db).list_recent(customer_id=customer_id, limit=limit)
