from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.storage import (
    FixturePlacementDetail,
    FixturePlacementUpdate,
    StorageCodeOrganize,
    StorageCodeRegister,
    StorageContainerCreate,
    StorageContainerRead,
    StorageContainerUpdate,
    StorageOverviewRead,
)
from backend.app.services.storage_service import StorageService


router = APIRouter(prefix="/storage", tags=["storage"], dependencies=[Depends(require_permission("read"))])


def _http_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found") else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=message)


@router.get("/overview", response_model=StorageOverviewRead)
def get_storage_overview(
    customer_id: int = Query(...),
    keyword: str = Query("", max_length=160),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return StorageService(db).get_overview(customer_id, keyword)


@router.post(
    "/containers",
    response_model=StorageContainerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("write"))],
)
def create_storage_container(
    payload: StorageContainerCreate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    try:
        return StorageService(db).create_container(payload, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.put(
    "/containers/{container_id}",
    response_model=StorageContainerRead,
    dependencies=[Depends(require_permission("write"))],
)
def update_storage_container(
    container_id: int,
    payload: StorageContainerUpdate,
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        return StorageService(db).update_container(container_id, customer_id, payload, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.delete(
    "/containers/{container_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("write"))],
)
def delete_storage_container(
    container_id: int,
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    try:
        StorageService(db).delete_container(container_id, customer_id, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/codes/organize",
    response_model=StorageOverviewRead,
    dependencies=[Depends(require_permission("write"))],
)
def organize_storage_codes(
    payload: StorageCodeOrganize,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    try:
        return StorageService(db).organize_codes(payload, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/codes/register",
    response_model=StorageOverviewRead,
    dependencies=[Depends(require_permission("write"))],
)
def register_storage_codes(
    payload: StorageCodeRegister,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolve_customer_scope(session, db, payload.customer_id, allow_empty=False)
    try:
        return StorageService(db).register_codes(payload, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.get("/fixtures/{fixture_id}/placements", response_model=FixturePlacementDetail)
def get_fixture_placements(
    fixture_id: int,
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    service = StorageService(db)
    try:
        customer_id = service.get_fixture_customer_id(fixture_id)
        resolve_customer_scope(session, db, customer_id, allow_empty=False)
        return service.get_fixture_placements(fixture_id)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/fixtures/{fixture_id}/sync",
    response_model=FixturePlacementDetail,
    dependencies=[Depends(require_permission("write"))],
)
def sync_fixture_placements(
    fixture_id: int,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    service = StorageService(db)
    try:
        customer_id = service.get_fixture_customer_id(fixture_id)
        resolve_customer_scope(session, db, customer_id, allow_empty=False)
        return service.resync_fixture(fixture_id, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.put(
    "/fixtures/{fixture_id}/placements",
    response_model=FixturePlacementDetail,
    dependencies=[Depends(require_permission("write"))],
)
def replace_fixture_placements(
    fixture_id: int,
    payload: FixturePlacementUpdate,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    service = StorageService(db)
    try:
        customer_id = service.get_fixture_customer_id(fixture_id)
        resolve_customer_scope(session, db, customer_id, allow_empty=False)
        return service.replace_fixture_placements(fixture_id, payload, actor=session)
    except ValueError as exc:
        raise _http_error(exc) from exc
