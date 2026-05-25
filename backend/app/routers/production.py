from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.production import CapacityRead, FixtureRequirementCreate, FixtureRequirementRead
from backend.app.services.production_service import ProductionService

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/fixture-requirements", response_model=FixtureRequirementRead, status_code=status.HTTP_201_CREATED)
def upsert_fixture_requirement(payload: FixtureRequirementCreate, db: Session = Depends(get_db)):
    service = ProductionService(db)
    try:
        return service.create_fixture_requirement(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/capacity/stations/{station_id}", response_model=CapacityRead)
def get_station_capacity(station_id: int, db: Session = Depends(get_db)):
    service = ProductionService(db)
    try:
        return service.get_station_capacity(station_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
