from typing import Literal

from backend.app.schemas.common import ORMModel
from backend.app.schemas.inventory import IdentifierStockSummaryRead, StockSummaryRead, StockTransactionRead
from backend.app.schemas.master import FixtureRead, MachineModelRead
from backend.app.schemas.production import ModelQueryRead


class GlobalSearchResult(ORMModel):
    entity_type: Literal["fixture", "model", "station"]
    title: str
    subtitle: str | None
    reference_id: int
    is_active: bool
    stock_qty: int | None = None
    stock_status: str | None = None
    location_code: str | None = None
    matched_identifier: str | None = None


class GlobalSearchResultPage(ORMModel):
    items: list[GlobalSearchResult]
    page: int
    page_size: int
    total: int
    has_more: bool


class SearchFixtureStationRowRead(ORMModel):
    model_id: int
    model_code: str
    model_name: str
    station_id: int
    station_code: str
    station_name: str
    required_qty: int


class SearchFixtureContextRead(ORMModel):
    fixture: FixtureRead
    stock: StockSummaryRead | None
    identifier_rows: list[IdentifierStockSummaryRead]
    related_models: list[MachineModelRead]
    station_rows: list[SearchFixtureStationRowRead]
    transactions: list[StockTransactionRead]


class SearchModelContextRead(ORMModel):
    model: MachineModelRead
    query: ModelQueryRead
