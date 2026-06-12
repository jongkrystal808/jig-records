from typing import Literal

from backend.app.schemas.common import ORMModel


class GlobalSearchResult(ORMModel):
    entity_type: Literal["fixture", "model", "station", "serial"]
    title: str
    subtitle: str | None
    reference_id: int
    stock_qty: int | None = None
    stock_status: str | None = None
    location_code: str | None = None
