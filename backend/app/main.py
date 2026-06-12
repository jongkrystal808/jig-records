from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from backend.app.core.config import settings
from backend.app.core.errors import register_error_handlers
from backend.app.core.migrations import upgrade_database
from backend.app.routers import api_router
from backend.app.services.auth_service import AuthService
from backend.app.core.database import SessionLocal


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    register_error_handlers(app)

    @app.on_event("startup")
    def on_startup() -> None:
        upgrade_database()
        db = SessionLocal()
        try:
            AuthService(db).ensure_default_user()
        finally:
            db.close()

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_v2_prefix)
    return app


app = create_app()
