from fastapi import FastAPI
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.errors import register_error_handlers
from backend.app.core.logging import setup_logging
from backend.app.core.migrations import verify_runtime_migration_gate
from backend.app.routers import api_router


def create_app() -> FastAPI:
    setup_logging()
    settings.validate_runtime_safety()
    verify_runtime_migration_gate(source="app_startup")
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    register_error_handlers(app)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/health")
    def health() -> dict[str, str]:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database is unavailable",
            ) from exc
        finally:
            db.close()
        return {"status": "ok", "database": "ok"}

    app.include_router(api_router, prefix=settings.api_v2_prefix)
    return app


app = create_app()
