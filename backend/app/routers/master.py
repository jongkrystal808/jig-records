from fastapi.responses import FileResponse, StreamingResponse
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, get_allowed_customer_ids, list_accessible_customers, list_accessible_customers_page, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.auth import UserRead
from backend.app.schemas.common import CsvImportPayload, ImportResultRead
from backend.app.schemas.master import (
    CustomerCreate,
    CustomerPageRead,
    CustomerRead,
    CustomerUpdate,
    FixtureCreate,
    FixtureDeleteRead,
    FixtureImageBatchUploadRead,
    FixtureImageUploadRead,
    FixturePageRead,
    FixtureQualityReportRead,
    FixtureRead,
    FixtureUpdate,
    MachineModelCreate,
    MachineModelDeleteRead,
    MachineModelRead,
    MachineModelPageRead,
    MachineModelUpdate,
    StationCreate,
    StationDeleteRead,
    StationRead,
    StationPageRead,
    StationUpdate,
)
from backend.app.services.master_service import MasterService
from backend.app.services.auth_service import AuthService
from backend.app.utils.fixture_images import guess_fixture_image_media_type

router = APIRouter(prefix="/master", tags=["master"], dependencies=[Depends(require_permission("read"))])


@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("super_manage"))],
)
def create_customer(
    payload: CustomerCreate,
    session: SessionContext = Depends(require_permission("super_manage")),
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
    dependencies=[Depends(require_permission("super_manage"))],
)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: SessionContext = Depends(require_permission("super_manage")),
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


@router.get("/customers/page", response_model=CustomerPageRead)
def list_customers_page(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str = Query("", max_length=160),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    return list_accessible_customers_page(
        session,
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
    )


@router.get("/customers/{customer_id}/users", response_model=list[UserRead])
def list_customer_users(
    customer_id: int,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return AuthService(db).list_users_by_customer(customer_id)


@router.get("/form-export")
def export_form_master_data(
    entity: str = Query(..., pattern="^(fixture|model|station|customer|fixture-images)$"),
    customer_id: int | None = Query(default=None),
    keyword: str = Query("", max_length=160),
    status_filter: str = Query("all", pattern="^(all|active|inactive)$"),
    image_status: str = Query("all", pattern="^(all|with-image|missing-image)$"),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    accessible_customer_ids = None
    if entity == "customer":
        accessible_customer_ids = get_allowed_customer_ids(session, db)
    else:
        if customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="customer_id is required",
            )
        customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    is_active = None if status_filter == "all" else status_filter == "active"
    content = MasterService(db).stream_form_export_csv(
        entity=entity,
        customer_id=customer_id,
        keyword=keyword,
        is_active=is_active,
        image_status=image_status,
        accessible_customer_ids=accessible_customer_ids,
    )
    return StreamingResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="form-{entity}.csv"'},
    )


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


@router.get("/fixtures/page", response_model=FixturePageRead)
def list_fixtures_page(
    customer_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str = Query("", max_length=160),
    status_filter: str = Query("all", pattern="^(all|active|inactive)$"),
    image_status: str = Query("all", pattern="^(all|with-image|missing-image)$"),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    is_active = None if status_filter == "all" else status_filter == "active"
    return MasterService(db).list_fixtures_page(
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active,
        image_status=image_status,
    )


@router.get("/fixtures/quality", response_model=FixtureQualityReportRead, dependencies=[Depends(require_permission("manage"))])
def get_fixture_quality_report(
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return MasterService(db).build_fixture_quality_report(customer_id)


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
    service = MasterService(db)
    try:
        current_customer_id = service.get_fixture_customer_id(fixture_id)
        resolve_customer_scope(session, db, current_customer_id, allow_empty=False)
        resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
        return service.update_fixture(fixture_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post(
    "/fixtures/{fixture_id}/image",
    response_model=FixtureImageUploadRead,
    dependencies=[Depends(require_permission("write"))],
)
async def upload_fixture_image(
    fixture_id: int,
    customer_id: int = Query(...),
    image: UploadFile = File(...),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        return service.upload_fixture_image(
            fixture_id,
            customer_id=customer_id,
            content=await image.read(),
            content_type=image.content_type,
            filename=image.filename,
            actor=session,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post(
    "/fixtures/images/batch",
    response_model=FixtureImageBatchUploadRead,
    dependencies=[Depends(require_permission("write"))],
)
async def upload_fixture_images_batch(
    customer_id: int = Query(...),
    images: list[UploadFile] = File(...),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = MasterService(db)
    try:
        uploads = []
        for image in images:
            uploads.append(
                {
                    "filename": image.filename,
                    "content_type": image.content_type,
                    "content": await image.read(),
                }
            )
        return service.upload_fixture_images_batch(customer_id=customer_id, uploads=uploads, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.delete(
    "/fixtures/{fixture_id}",
    response_model=FixtureDeleteRead,
    dependencies=[Depends(require_permission("manage"))],
)
def delete_fixture(
    fixture_id: int,
    customer_id: int = Query(...),
    delete_transactions: bool = Query(default=False),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        return MasterService(db).delete_fixture(
            fixture_id,
            customer_id=customer_id,
            delete_transactions=delete_transactions,
            actor=session,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/fixtures/{fixture_code}/image")
def fixture_image_by_code(
    fixture_code: str,
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    image_path = MasterService(db).get_fixture_image_path(fixture_code, customer_id=customer_id)
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


@router.get("/models/page", response_model=MachineModelPageRead)
def list_models_page(
    customer_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str = Query("", max_length=160),
    status_filter: str = Query("all", pattern="^(all|active|inactive)$"),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    is_active = None if status_filter == "all" else status_filter == "active"
    return MasterService(db).list_models_page(customer_id=customer_id, page=page, page_size=page_size, keyword=keyword, is_active=is_active)


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


@router.delete(
    "/models/{model_id}",
    response_model=MachineModelDeleteRead,
    dependencies=[Depends(require_permission("manage"))],
)
def delete_model(
    model_id: int,
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        return MasterService(db).delete_model(model_id, customer_id=customer_id, actor=session)
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


@router.get("/stations/page", response_model=StationPageRead)
def list_stations_page(
    customer_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str = Query("", max_length=160),
    status_filter: str = Query("all", pattern="^(all|active|inactive)$"),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    is_active = None if status_filter == "all" else status_filter == "active"
    return MasterService(db).list_stations_page(customer_id=customer_id, page=page, page_size=page_size, keyword=keyword, is_active=is_active)


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


@router.delete(
    "/stations/{station_id}",
    response_model=StationDeleteRead,
    dependencies=[Depends(require_permission("manage"))],
)
def delete_station(
    station_id: int,
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        return MasterService(db).delete_station(station_id, customer_id=customer_id, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc
