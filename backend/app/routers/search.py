from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.search import GlobalSearchResult
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(require_permission("read"))])


@router.get("/global", response_model=list[GlobalSearchResult])
def global_search(
    q: str = Query(..., min_length=1, description="Fixture code/name, model, station, location, serial"),
    customer_id: int | None = Query(default=None),
    session: SessionContext = Depends(require_permission("read")),
    db: Session = Depends(get_db),
):
    customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    return SearchService(db).global_search(q, customer_id=customer_id)

