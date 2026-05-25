from fastapi import FastAPI

from backend.app.core.config import settings
from backend.app.core.database import engine
from backend.app.models import Base
from backend.app.routers import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_v2_prefix)
    return app


app = create_app()
