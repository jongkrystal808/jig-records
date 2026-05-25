from fastapi import APIRouter

from backend.app.routers import inventory, master, production, search, warehouse

api_router = APIRouter()
api_router.include_router(master.router)
api_router.include_router(inventory.router)
api_router.include_router(production.router)
api_router.include_router(warehouse.router)
api_router.include_router(search.router)
