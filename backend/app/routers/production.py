from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.common import CsvImportPayload
from backend.app.schemas.production import (
    CapacityRead,
    FixtureRequirementCreate,
    FixtureRequirementCopy,
    FixtureRequirementCopyResult,
    FixtureRequirementListItemRead,
    FixtureRequirementPageRead,
    FixtureRequirementRead,
    ModelQueryRead,
    ModelStationCreate,
    ModelStationRead,
    ModelStationPageRead,
    ProductionCsvImportPayload,
    ProductionImportPreviewRead,
    ProductionImportResultRead,
)
from backend.app.services.production_service import ProductionService

router = APIRouter(prefix="/production", tags=["production"], dependencies=[Depends(require_permission("read"))])


@router.post(
    "/model-stations",
    response_model=ModelStationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("write"))],
)
def create_model_station(
    payload: ModelStationCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.create_model_station(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/model-stations/{row_id}", response_model=ModelStationRead, dependencies=[Depends(require_permission("write"))])
def update_model_station(
    row_id: int,
    payload: ModelStationCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.update_model_station(row_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.delete("/model-stations/{row_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("write"))])
def delete_model_station(
    row_id: int,
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        service.delete_model_station(row_id, customer_id=customer_id, actor=session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/model-stations", response_model=list[ModelStationRead])
def list_model_stations(
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return ProductionService(db).list_model_stations(customer_id=customer_id)


@router.get("/model-stations/page", response_model=ModelStationPageRead)
def list_model_stations_page(
    customer_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    model_id: int | None = Query(None),
    station_id: int | None = Query(None),
    keyword: str = Query("", max_length=160),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return ProductionService(db).list_model_stations_page(customer_id=customer_id, page=page, page_size=page_size, model_id=model_id, station_id=station_id, keyword=keyword)


@router.get("/form-export")
def export_form_production_data(
    entity: str = Query(..., pattern="^(requirements|mappings)$"),
    customer_id: int = Query(...),
    model_id: int | None = Query(None),
    station_id: int | None = Query(None),
    keyword: str = Query("", max_length=160),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    content = ProductionService(db).stream_form_export_csv(
        entity=entity,
        customer_id=customer_id,
        model_id=model_id,
        station_id=station_id,
        keyword=keyword,
    )
    return StreamingResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="form-{entity}.csv"'},
    )


@router.get("/model-stations/export")
def export_model_stations(
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    content = ProductionService(db).export_model_stations_csv(customer_id=customer_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="model-stations.csv"'},
    )


@router.get("/model-stations/template")
def model_station_template(db: Session = Depends(get_db)):
    content = ProductionService(db).model_station_template_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="model-stations-template.csv"'},
    )


@router.post(
    "/model-stations/import/preview",
    response_model=ProductionImportPreviewRead,
    dependencies=[Depends(require_permission("write"))],
)
def preview_model_stations_import(
    customer_id: int | None = None,
    payload: CsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        return ProductionService(db).preview_model_stations_csv(customer_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/model-stations/import", response_model=ProductionImportResultRead, dependencies=[Depends(require_permission("write"))])
def import_model_stations(
    customer_id: int | None = None,
    payload: ProductionCsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.import_model_stations_csv(customer_id, payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/fixture-requirements",
    response_model=FixtureRequirementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("write"))],
)
def upsert_fixture_requirement(
    payload: FixtureRequirementCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.create_fixture_requirement(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/fixture-requirements/copy",
    response_model=FixtureRequirementCopyResult,
    dependencies=[Depends(require_permission("write"))],
)
def copy_fixture_requirements(
    payload: FixtureRequirementCopy,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.copy_fixture_requirements(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put(
    "/fixture-requirements/{requirement_id}",
    response_model=FixtureRequirementRead,
    dependencies=[Depends(require_permission("write"))],
)
def update_fixture_requirement(
    requirement_id: int,
    payload: FixtureRequirementCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.update_fixture_requirement(requirement_id, payload, actor=session)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.delete(
    "/fixture-requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("write"))],
)
def delete_fixture_requirement(
    requirement_id: int,
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        service.delete_fixture_requirement(requirement_id, customer_id=customer_id, actor=session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/fixture-requirements", response_model=list[FixtureRequirementListItemRead])
def list_fixture_requirements(
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return ProductionService(db).list_fixture_requirements(customer_id=customer_id)


@router.get("/fixture-requirements/page", response_model=FixtureRequirementPageRead)
def list_fixture_requirements_page(
    customer_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    model_id: int | None = Query(None),
    station_id: int | None = Query(None),
    keyword: str = Query("", max_length=160),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return ProductionService(db).list_fixture_requirements_page(customer_id=customer_id, page=page, page_size=page_size, model_id=model_id, station_id=station_id, keyword=keyword)


@router.get("/fixture-requirements/export")
def export_fixture_requirements(
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    content = ProductionService(db).export_fixture_requirements_csv(customer_id=customer_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="fixture-requirements.csv"'},
    )


@router.get("/fixture-requirements/template")
def fixture_requirement_template(db: Session = Depends(get_db)):
    content = ProductionService(db).fixture_requirement_template_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="fixture-requirements-template.csv"'},
    )


@router.post(
    "/fixture-requirements/import/preview",
    response_model=ProductionImportPreviewRead,
    dependencies=[Depends(require_permission("write"))],
)
def preview_fixture_requirements_import(
    customer_id: int | None = None,
    payload: CsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        return ProductionService(db).preview_fixture_requirements_csv(customer_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/fixture-requirements/import", response_model=ProductionImportResultRead, dependencies=[Depends(require_permission("write"))])
def import_fixture_requirements(
    customer_id: int | None = None,
    payload: ProductionCsvImportPayload = ...,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.import_fixture_requirements_csv(customer_id, payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/capacity/stations/{station_id}", response_model=CapacityRead)
def get_station_capacity(
    station_id: int,
    model_id: int,
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.get_station_capacity(station_id, model_id=model_id, customer_id=customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/models/{model_id}/query", response_model=ModelQueryRead)
def get_model_query(
    model_id: int,
    station_id: int | None = None,
    customer_id: int | None = None,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    service = ProductionService(db)
    try:
        return service.get_model_query(model_id, station_id=station_id, customer_id=customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

