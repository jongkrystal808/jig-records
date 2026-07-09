from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.search import GlobalSearchResultPage, SearchFixtureContextRead, SearchModelContextRead
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(require_permission("read"))])


@router.get("/global", response_model=GlobalSearchResultPage)
def global_search(
    q: str = Query(..., min_length=1, description="Fixture code/name, model, station, location, serial"),
    customer_id: int | None = Query(default=None),
    entity_type: Literal["fixture", "model", "station"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return SearchService(db).global_search(
        q,
        customer_id=customer_id,
        entity_type=entity_type,
        page=page,
        page_size=page_size,
    )


@router.get("/fixtures/{fixture_id}/context", response_model=SearchFixtureContextRead)
def get_fixture_context(
    fixture_id: int,
    customer_id: int = Query(...),
    recent_transaction_limit: int = Query(default=8, ge=1, le=50),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return SearchService(db).get_fixture_context(
        fixture_id,
        customer_id=customer_id,
        recent_transaction_limit=recent_transaction_limit,
    )


@router.get("/models/{model_id}/context", response_model=SearchModelContextRead)
def get_model_context(
    model_id: int,
    customer_id: int = Query(...),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return SearchService(db).get_model_context(model_id, customer_id=customer_id)

