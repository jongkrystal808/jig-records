from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.master import (
    CustomerCreate,
    CustomerRead,
    FixtureCreate,
    FixtureRead,
    MachineModelCreate,
    MachineModelRead,
    OwnerCreate,
    OwnerRead,
    StationCreate,
    StationRead,
)
from backend.app.services.master_service import MasterService

router = APIRouter(prefix="/master", tags=["master"])


@router.post("/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    service = MasterService(db)
    try:
        return service.create_customer(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return MasterService(db).list_customers()


@router.post("/fixtures", response_model=FixtureRead, status_code=status.HTTP_201_CREATED)
def create_fixture(payload: FixtureCreate, db: Session = Depends(get_db)):
    service = MasterService(db)
    try:
        return service.create_fixture(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/fixtures", response_model=list[FixtureRead])
def list_fixtures(db: Session = Depends(get_db)):
    return MasterService(db).list_fixtures()


@router.post("/models", response_model=MachineModelRead, status_code=status.HTTP_201_CREATED)
def create_model(payload: MachineModelCreate, db: Session = Depends(get_db)):
    service = MasterService(db)
    try:
        return service.create_model(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/models", response_model=list[MachineModelRead])
def list_models(db: Session = Depends(get_db)):
    return MasterService(db).list_models()


@router.post("/stations", response_model=StationRead, status_code=status.HTTP_201_CREATED)
def create_station(payload: StationCreate, db: Session = Depends(get_db)):
    service = MasterService(db)
    try:
        return service.create_station(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/stations", response_model=list[StationRead])
def list_stations(db: Session = Depends(get_db)):
    return MasterService(db).list_stations()


@router.post("/owners", response_model=OwnerRead, status_code=status.HTTP_201_CREATED)
def create_owner(payload: OwnerCreate, db: Session = Depends(get_db)):
    service = MasterService(db)
    try:
        return service.create_owner(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/owners", response_model=list[OwnerRead])
def list_owners(db: Session = Depends(get_db)):
    return MasterService(db).list_owners()
