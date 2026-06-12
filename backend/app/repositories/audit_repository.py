from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_log(
        self,
        *,
        customer_id: int | None,
        entity_type: str,
        entity_key: str,
        action: str,
        summary: str,
        actor_user_id: int | None,
        actor_username: str,
        actor_display_name: str,
        actor_role: str,
    ) -> AuditLog:
        log = AuditLog(
            customer_id=customer_id,
            entity_type=entity_type,
            entity_key=entity_key,
            action=action,
            summary=summary,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            actor_display_name=actor_display_name,
            actor_role=actor_role,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_recent_logs(self, customer_id: int | None = None, limit: int = 10) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
        if customer_id is not None:
            stmt = stmt.where(AuditLog.customer_id == customer_id)
        return list(self.db.scalars(stmt))
