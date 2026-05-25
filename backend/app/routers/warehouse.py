from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.warehouse import (
    FixtureImageCreate,
    FixtureImageRead,
    FixtureLocationAssignmentCreate,
    FixtureLocationAssignmentRead,
    StorageLocationCreate,
    StorageLocationRead,
)
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


@router.post("/location-assignments", response_model=FixtureLocationAssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_fixture_location(payload: FixtureLocationAssignmentCreate, db: Session = Depends(get_db)):
    service = WarehouseService(db)
    try:
        return service.assign_fixture_location(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/location-assignments", response_model=list[FixtureLocationAssignmentRead])
def list_assignments(db: Session = Depends(get_db)):
    return WarehouseService(db).list_assignments()


@router.post("/fixture-images", response_model=FixtureImageRead, status_code=status.HTTP_201_CREATED)
def create_fixture_image(payload: FixtureImageCreate, db: Session = Depends(get_db)):
    service = WarehouseService(db)
    try:
        return service.create_fixture_image(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/fixture-images", response_model=list[FixtureImageRead])
def list_fixture_images(fixture_id: int | None = None, db: Session = Depends(get_db)):
    return WarehouseService(db).list_fixture_images(fixture_id=fixture_id)
