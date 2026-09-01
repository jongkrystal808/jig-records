from fastapi import APIRouter

from backend.app.routers import auth, audit, inventory, master, production, search, storage

api_router = APIRouter()
api_router.include_router(master.router)
api_router.include_router(auth.router)
api_router.include_router(audit.router)
api_router.include_router(inventory.router)
api_router.include_router(production.router)
api_router.include_router(search.router)
api_router.include_router(storage.router)
