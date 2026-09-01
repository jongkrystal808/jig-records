from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.master import Customer, User, UserCustomer

PermissionLevel = Literal["read", "write", "manage", "super_manage"]
SessionMode = Literal["user", "guest"]


@dataclass(frozen=True)
class SessionContext:
    mode: SessionMode
    user_id: int | None
    username: str | None
    display_name: str
    role: str
    issued_at: int
    expires_at: int

    @property
    def is_guest(self) -> bool:
        return self.mode == "guest"


def _get_db():
    from backend.app.core.database import get_db

    yield from get_db()


def _base64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _base64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def _sign(payload: str) -> str:
    digest = hmac.new(settings.auth_secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def create_session_token(*, mode: SessionMode, user: User | None = None, display_name: str | None = None) -> str:
    issued_at = int(time.time())
    expires_at = issued_at + settings.auth_token_ttl_seconds
    payload = {
        "mode": mode,
        "sub": None if user is None else user.id,
        "username": None if user is None else user.username,
        "display_name": display_name if display_name is not None else (None if user is None else user.display_name),
        "role": None if user is None else user.role,
        "iat": issued_at,
        "exp": expires_at,
    }
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def _decode_session_token(token: str) -> dict:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication token") from exc

    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication token")

    try:
        payload = json.loads(_base64url_decode(encoded_payload))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication token") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication token")

    now = int(time.time())
    expires_at = int(payload.get("exp") or 0)
    if expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session has expired")

    return payload


def _load_context_from_payload(payload: dict, db: Session) -> SessionContext:
    mode = payload.get("mode")
    display_name = str(payload.get("display_name") or "訪客")
    issued_at = int(payload.get("iat") or 0)
    expires_at = int(payload.get("exp") or 0)

    if mode == "guest":
        return SessionContext(
            mode="guest",
            user_id=None,
            username=None,
            display_name=display_name,
            role="guest",
            issued_at=issued_at,
            expires_at=expires_at,
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication token")

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user is inactive or missing")

    token_role = str(payload.get("role") or "")
    if token_role != user.role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication token is stale")

    token_username = str(payload.get("username") or "")
    if token_username != user.username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication token is stale")

    return SessionContext(
        mode="user",
        user_id=user.id,
        username=user.username,
        display_name=display_name or user.display_name,
        role=user.role,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def get_session_context(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(_get_db),
) -> SessionContext:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authentication token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authentication token")
    payload = _decode_session_token(token)
    return _load_context_from_payload(payload, db)


def try_get_session_context(authorization: str | None, db: Session | None = None) -> SessionContext | None:
    if authorization is None or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        payload = _decode_session_token(token)
        if db is not None:
            return _load_context_from_payload(payload, db)
        mode = payload.get("mode")
        display_name = str(payload.get("display_name") or "訪客")
        issued_at = int(payload.get("iat") or 0)
        expires_at = int(payload.get("exp") or 0)
        if mode == "guest":
            return SessionContext(
                mode="guest",
                user_id=None,
                username=None,
                display_name=display_name,
                role="guest",
                issued_at=issued_at,
                expires_at=expires_at,
            )
        return SessionContext(
            mode="user",
            user_id=None if payload.get("sub") is None else int(payload["sub"]),
            username=None if payload.get("username") is None else str(payload.get("username")),
            display_name=display_name,
            role=str(payload.get("role") or "unknown"),
            issued_at=issued_at,
            expires_at=expires_at,
        )
    except HTTPException:
        return None


def require_permission(level: PermissionLevel):
    def dependency(session: SessionContext = Depends(get_session_context)) -> SessionContext:
        if level == "read":
            return session
        if level == "write":
            if session.is_guest or session.role not in {"super_admin", "admin", "user"}:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="valid signed-in user role required")
            return session
        if level == "manage" and session.role not in {"super_admin", "admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin permission required")
        if level == "super_manage" and session.role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="super admin permission required")
        return session

    return dependency


def get_allowed_customer_ids(session: SessionContext, db: Session) -> list[int] | None:
    if session.is_guest:
        return None
    if session.user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="customer access is not available")
    stmt = select(UserCustomer.customer_id).where(UserCustomer.user_id == session.user_id).order_by(UserCustomer.customer_id)
    return list(db.scalars(stmt))


def _serialize_customer(customer: Customer, db: Session) -> dict:
    assigned_user_ids = list(
        db.scalars(select(UserCustomer.user_id).where(UserCustomer.customer_id == customer.id).order_by(UserCustomer.user_id))
    )
    return {
        "id": customer.id,
        "code": customer.code,
        "name": customer.name,
        "assigned_user_ids": assigned_user_ids,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


def list_accessible_customers(session: SessionContext, db: Session) -> list[dict]:
    if session.is_guest:
        stmt = select(Customer).order_by(Customer.code)
        return [_serialize_customer(customer, db) for customer in db.scalars(stmt)]
    allowed_customer_ids = get_allowed_customer_ids(session, db)
    if not allowed_customer_ids:
        return []
    stmt = select(Customer).where(Customer.id.in_(allowed_customer_ids)).order_by(Customer.code)
    return [_serialize_customer(customer, db) for customer in db.scalars(stmt)]


def list_accessible_customers_page(
    session: SessionContext,
    db: Session,
    *,
    page: int,
    page_size: int,
    keyword: str = "",
) -> dict:
    stmt = select(Customer)
    if not session.is_guest:
        allowed_customer_ids = get_allowed_customer_ids(session, db) or []
        if not allowed_customer_ids:
            return {"items": [], "page": page, "page_size": page_size, "total": 0}
        stmt = stmt.where(Customer.id.in_(allowed_customer_ids))
    normalized = keyword.strip()
    if normalized:
        pattern = f"%{normalized}%"
        stmt = stmt.where(or_(Customer.code.ilike(pattern), Customer.name.ilike(pattern)))

    total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
    customers = list(
        db.scalars(
            stmt.order_by(Customer.code)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    customer_ids = [customer.id for customer in customers]
    assigned_user_ids: dict[int, list[int]] = {customer_id: [] for customer_id in customer_ids}
    if customer_ids:
        for customer_id, user_id in db.execute(
            select(UserCustomer.customer_id, UserCustomer.user_id)
            .where(UserCustomer.customer_id.in_(customer_ids))
            .order_by(UserCustomer.customer_id, UserCustomer.user_id)
        ):
            assigned_user_ids[int(customer_id)].append(int(user_id))
    return {
        "items": [
            {
                "id": customer.id,
                "code": customer.code,
                "name": customer.name,
                "assigned_user_ids": assigned_user_ids[customer.id],
                "created_at": customer.created_at,
                "updated_at": customer.updated_at,
            }
            for customer in customers
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def resolve_customer_scope(
    session: SessionContext,
    db: Session,
    customer_id: int | None,
    *,
    allow_empty: bool = True,
) -> int | None:
    if session.is_guest:
        return customer_id
    allowed_customer_ids = get_allowed_customer_ids(session, db) or []
    if customer_id is None:
        if allow_empty:
            return None
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="customer_id is required")
    if customer_id not in allowed_customer_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="customer access denied")
    return customer_id
