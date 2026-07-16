from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext
from backend.app.core.logging import write_audit_log
from backend.app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    def record(
        self,
        *,
        customer_id: int | None,
        entity_type: str,
        entity_key: str,
        action: str,
        summary: str,
        actor: SessionContext | None,
    ) -> None:
        actor_user_id = None if actor is None else actor.user_id
        actor_username = "system" if actor is None or actor.username is None else actor.username
        actor_display_name = "系統" if actor is None else actor.display_name
        actor_role = "system" if actor is None else actor.role
        self.repo.create_log(
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
        write_audit_log(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "domain_audit",
                "actor": {
                    "user_id": actor_user_id,
                    "username": actor_username,
                    "display_name": actor_display_name,
                    "role": actor_role,
                },
                "entity": {
                    "customer_id": customer_id,
                    "type": entity_type,
                    "key": entity_key,
                },
                "action": action,
                "summary": summary,
            }
        )

    def list_recent(self, customer_id: int | None = None, limit: int = 10):
        return self.repo.list_recent_logs(customer_id=customer_id, limit=limit)
