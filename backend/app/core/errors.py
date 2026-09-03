from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from backend.app.core.audit_logging import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    request_id = uuid4().hex
    request.state.request_id = request_id
    return request_id


def _build_error_payload(
    code: str,
    message: str,
    *,
    request_id: str,
    details: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {"code": code, "message": message, "request_id": request_id}
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


def _sanitize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Exception):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_json_value(item) for item in value]
    return str(value)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = _get_request_id(request)
        code = "http_error"
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "unauthorized"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "forbidden"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
        elif exc.status_code == status.HTTP_409_CONFLICT:
            code = "conflict"
        elif exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
            code = "validation_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(code, str(exc.detail), request_id=request_id),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = _get_request_id(request)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_build_error_payload(
                "validation_error",
                "欄位驗證失敗",
                request_id=request_id,
                details=_sanitize_json_value(exc.errors()),
            ),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        request_id = _get_request_id(request)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_build_error_payload(
                "integrity_error",
                "資料儲存失敗，請確認欄位是否重複或違反關聯限制。",
                request_id=request_id,
            ),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = _get_request_id(request)
        request.state.unhandled_error_type = type(exc).__name__
        logger.exception(
            json.dumps(
                {
                    "event": "unhandled_request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "exception_type": type(exc).__name__,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_payload(
                "internal_error",
                "系統發生未預期錯誤",
                request_id=request_id,
            ),
            headers={REQUEST_ID_HEADER: request_id},
        )
