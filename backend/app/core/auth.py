from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.master import User

PermissionLevel = Literal["read", "write", "manage"]
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


def require_permission(level: PermissionLevel):
    def dependency(session: SessionContext = Depends(get_session_context)) -> SessionContext:
        if level == "read":
            return session
        if level == "write":
            if session.is_guest:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="guest sessions are read-only")
            return session
        if session.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin permission required")
        return session

    return dependency
