from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import FastAPI, Request

from backend.app.core.auth import try_get_session_context
from backend.app.core.logging import write_audit_log

REQUEST_ID_HEADER = "X-Request-ID"
_SENSITIVE_QUERY_MARKERS = (
    "authorization",
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
)


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    request_id = uuid4().hex
    request.state.request_id = request_id
    return request_id


def _safe_query_string(request: Request) -> str:
    return urlencode(
        [
            (
                key,
                "[REDACTED]"
                if any(marker in key.casefold() for marker in _SENSITIVE_QUERY_MARKERS)
                else value,
            )
            for key, value in request.query_params.multi_items()
        ],
        doseq=True,
    )


def register_audit_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def audit_request(request: Request, call_next):
        started_at = perf_counter()
        timestamp = datetime.now(timezone.utc)
        request_id = _request_id(request)
        response = None
        error_type = None

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            error_type = error_type or getattr(request.state, "unhandled_error_type", None)
            session = try_get_session_context(request.headers.get("Authorization"))
            client = request.client
            write_audit_log(
                {
                    "timestamp": timestamp.isoformat(),
                    "event_type": "request_audit",
                    "request_id": request_id,
                    "actor": {
                        "mode": None if session is None else session.mode,
                        "user_id": None if session is None else session.user_id,
                        "username": None if session is None else session.username,
                        "display_name": "anonymous" if session is None else session.display_name,
                        "role": "anonymous" if session is None else session.role,
                    },
                    "request": {
                        "method": request.method,
                        "path": request.url.path,
                        "query": _safe_query_string(request),
                        "client_ip": None if client is None else client.host,
                    },
                    "response": {
                        "status_code": 500 if response is None else response.status_code,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    },
                    "error_type": error_type,
                }
            )
