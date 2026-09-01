from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.common import CsvImportPayload, ORMModel


class ProductionCsvImportPayload(CsvImportPayload):
    overwrite_existing: bool = False


class ProductionImportPreviewRow(BaseModel):
    line: int
    model_code: str
    station_code: str
    fixture_code: str | None = None
    incoming_required_qty: int | None = None
    existing_required_qty: int | None = None
    status: Literal["new", "unchanged", "conflict", "error"]
    message: str


class ProductionImportPreviewRead(BaseModel):
    rows: list[ProductionImportPreviewRow]
    new_count: int
    unchanged_count: int
    conflict_count: int
    error_count: int


class ProductionImportResultRead(BaseModel):
    imported_count: int
    created_count: int
    updated_count: int
    skipped_count: int


class ModelStationCreate(BaseModel):
    customer_id: int
    model_id: int
    station_id: int


class ModelStationRead(ORMModel):
    id: int
    model_id: int
    station_id: int


class ModelStationListItemRead(ModelStationRead):
    model_code: str
    model_name: str
    station_code: str
    station_name: str


class ModelStationPageRead(BaseModel):
    items: list[ModelStationListItemRead]
    page: int
    page_size: int
    total: int


class FixtureRequirementCreate(BaseModel):
    customer_id: int
    model_id: int
    station_id: int
    fixture_id: int
    required_qty: int = Field(gt=0)
    designated_mode: bool = False
    designated_identifiers: list[str] = Field(default_factory=list)


class FixtureRequirementRead(ORMModel):
    id: int
    model_id: int
    station_id: int
    fixture_id: int
    required_qty: int
    designated_mode: bool
    designated_identifiers: list[str]


class FixtureRequirementCopy(BaseModel):
    customer_id: int
    source_model_id: int
    source_station_id: int
    target_model_id: int
    target_station_id: int
    overwrite_existing: bool = False


class FixtureRequirementCopyResult(BaseModel):
    source_requirement_count: int
    created_count: int
    updated_count: int
    skipped_count: int
    mapping_created: bool


class FixtureRequirementListItemRead(ORMModel):
    id: int
    model_id: int
    model_code: str
    station_id: int
    station_code: str
    fixture_id: int
    fixture_code: str
    fixture_name: str
    required_qty: int
    designated_mode: bool
    designated_identifiers: list[str]


class FixtureRequirementFormItemRead(FixtureRequirementListItemRead):
    stock_qty: int


class FixtureRequirementPageRead(BaseModel):
    items: list[FixtureRequirementFormItemRead]
    page: int
    page_size: int
    total: int


class CapacityRead(ORMModel):
    model_id: int
    model_code: str
    station_id: int
    station_code: str
    station_name: str
    max_open_station_count: int
    bottleneck_fixture_code: str | None


class ModelFixtureRequirementRead(ORMModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    stock_qty: int
    min_stock_qty: int
    required_per_station: int
    max_open_station_count: int
    stock_status: str


class ModelQueryStationRead(ORMModel):
    station_id: int
    station_code: str
    station_name: str
    max_open_station_count: int
    bottleneck_fixture_code: str | None


class ModelQueryStationRequirementRead(ORMModel):
    model_id: int
    model_code: str
    station_id: int
    station_code: str
    fixture_id: int
    fixture_code: str
    fixture_name: str
    required_qty: int
    designated_mode: bool
    designated_identifiers: list[str]
    stock_qty: int
    max_open_station_count: int
    stock_status: str


class ModelQueryRead(ORMModel):
    model_id: int
    model_code: str
    model_name: str
    max_open_station_count: int
    station_count: int
    fixture_type_count: int
    total_stock_qty: int
    stations: list[ModelQueryStationRead]
    station_requirements: list[ModelQueryStationRequirementRead]
    fixtures: list[ModelFixtureRequirementRead]
