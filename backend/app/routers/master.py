from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, list_accessible_customers, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.auth import UserRead
from backend.app.schemas.common import CsvImportPayload, ImportResultRead
from backend.app.schemas.master import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    FixtureCreate,
    FixtureRead,
    FixtureUpdate,
    MachineModelCreate,
    MachineModelRead,
    MachineModelUpdate,
    StationCreate,
    StationRead,
    StationUpdate,
)
from backend.app.services.master_service import MasterService
from backend.app.services.auth_service import AuthService
from backend.app.utils.fixture_images import guess_fixture_image_media_type, resolve_fixture_image_path

router = APIRouter(prefix="/master", tags=["master"], dependencies=[Depends(require_permission("read"))])


@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("manage"))],
)
def create_customer(
    payload: CustomerCreate,
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    service = MasterService(db)
    try:
        return service.create_customer(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put(
    "/customers/{customer_id}",
    response_model=CustomerRead,
    dependencies=[Depends(require_permission("manage"))],
)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    service = MasterService(db)
    try:
        return service.update_customer(customer_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(session: SessionContext = Depends(require_permission("read")), db: Session = Depends(get_db)):
    return list_accessible_customers(session, db)


@router.get("/customers/{customer_id}/users", response_model=list[UserRead])
def list_customer_users(
    customer_id: int,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return AuthService(db).list_users_by_customer(customer_id)


@router.post(
    "/fixtures",
    response_model=FixtureRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("write"))],
)
def create_fixture(
    payload: FixtureCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.create_fixture(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/fixtures", response_model=list[FixtureRead])
def list_fixtures(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return MasterService(db).list_fixtures(customer_id=customer_id)


@router.get("/fixtures/export")
def export_fixtures(
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, customer_id, allow_empty=False)
    content = MasterService(db).export_fixtures_csv(customer_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="fixtures.csv"'},
    )


@router.get("/fixtures/template")
def fixture_template(db: Session = Depends(get_db)):
    content = MasterService(db).fixture_template_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="fixtures-template.csv"'},
    )


@router.post("/fixtures/import", response_model=ImportResultRead, dependencies=[Depends(require_permission("write"))])
def import_fixtures(
    customer_id: int = Query(...),
    payload: CsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return {"imported_count": service.import_fixtures_csv(customer_id, payload, actor=session)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/fixtures/{fixture_id}", response_model=FixtureRead, dependencies=[Depends(require_permission("write"))])
def update_fixture(
    fixture_id: int,
    payload: FixtureUpdate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.update_fixture(fixture_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/fixtures/{fixture_code}/image")
def fixture_image_by_code(fixture_code: str):
    image_path = resolve_fixture_image_path(fixture_code)
    if image_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fixture image not found")
    return FileResponse(image_path, media_type=guess_fixture_image_media_type(image_path))


@router.post(
    "/models",
    response_model=MachineModelRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("write"))],
)
def create_model(
    payload: MachineModelCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.create_model(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/models", response_model=list[MachineModelRead])
def list_models(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return MasterService(db).list_models(customer_id=customer_id)


@router.get("/models/export")
def export_models(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    content = MasterService(db).export_models_csv(customer_id=customer_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="models.csv"'},
    )


@router.get("/models/template")
def model_template(db: Session = Depends(get_db)):
    content = MasterService(db).model_template_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="models-template.csv"'},
    )


@router.post("/models/import", response_model=ImportResultRead, dependencies=[Depends(require_permission("write"))])
def import_models(
    customer_id: int | None = Query(default=None),
    payload: CsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return {"imported_count": service.import_models_csv(customer_id, payload, actor=session)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/models/{model_id}", response_model=MachineModelRead, dependencies=[Depends(require_permission("write"))])
def update_model(
    model_id: int,
    payload: MachineModelUpdate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.update_model(model_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post(
    "/stations",
    response_model=StationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("write"))],
)
def create_station(
    payload: StationCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.create_station(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/stations", response_model=list[StationRead])
def list_stations(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return MasterService(db).list_stations(customer_id=customer_id)


@router.get("/stations/export")
def export_stations(
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    content = MasterService(db).export_stations_csv(customer_id=customer_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="stations.csv"'},
    )


@router.get("/stations/template")
def station_template(db: Session = Depends(get_db)):
    content = MasterService(db).station_template_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="stations-template.csv"'},
    )


@router.post("/stations/import", response_model=ImportResultRead, dependencies=[Depends(require_permission("write"))])
def import_stations(
    customer_id: int | None = Query(default=None),
    payload: CsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return {"imported_count": service.import_stations_csv(customer_id, payload, actor=session)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/stations/{station_id}", response_model=StationRead, dependencies=[Depends(require_permission("write"))])
def update_station(
    station_id: int,
    payload: StationUpdate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.update_station(station_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc



