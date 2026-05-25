from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.search import GlobalSearchResult
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/global", response_model=list[GlobalSearchResult])
def global_search(
    q: str = Query(..., min_length=1, description="Fixture code/name, model, station, location, serial"),
    db: Session = Depends(get_db),
):
    return SearchService(db).global_search(q)
