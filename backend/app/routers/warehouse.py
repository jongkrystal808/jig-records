from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.warehouse import StorageLocationCreate, StorageLocationRead
from backend.app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.post("/locations", response_model=StorageLocationRead, status_code=status.HTTP_201_CREATED)
def create_location(payload: StorageLocationCreate, db: Session = Depends(get_db)):
    service = WarehouseService(db)
    try:
        return service.create_location(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/locations", response_model=list[StorageLocationRead])
def list_locations(db: Session = Depends(get_db)):
    return WarehouseService(db).list_locations()
