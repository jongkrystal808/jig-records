from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.audit import AuditLogRead
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_permission("read"))])


@router.get("/logs", response_model=list[AuditLogRead])
def list_audit_logs(
    customer_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return AuditService(db).list_recent(customer_id=customer_id, limit=limit)

