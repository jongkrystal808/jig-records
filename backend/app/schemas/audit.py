from backend.app.schemas.common import TimestampedResponse


class AuditLogRead(TimestampedResponse):
    id: int
    customer_id: int | None
    entity_type: str
    entity_key: str
    action: str
    summary: str
    actor_user_id: int | None
    actor_username: str
    actor_display_name: str
    actor_role: str
