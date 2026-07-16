from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

from fastapi import FastAPI, Request

from backend.app.core.auth import try_get_session_context
from backend.app.core.logging import write_audit_log


def register_audit_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def audit_request(request: Request, call_next):
        started_at = perf_counter()
        timestamp = datetime.now(timezone.utc)
        response = None
        error_message = None

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_message = str(exc)
            raise
        finally:
            session = try_get_session_context(request.headers.get("Authorization"))
            client = request.client
            write_audit_log(
                {
                    "timestamp": timestamp.isoformat(),
                    "event_type": "request_audit",
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
                        "query": str(request.url.query),
                        "client_ip": None if client is None else client.host,
                    },
                    "response": {
                        "status_code": 500 if response is None else response.status_code,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    },
                    "error": error_message,
                }
            )
