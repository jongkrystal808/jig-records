from pydantic import BaseModel, Field

from backend.app.schemas.common import ORMModel


class ModelStationCreate(BaseModel):
    customer_id: int
    model_id: int
    station_id: int


class ModelStationRead(ORMModel):
    id: int
    model_id: int
    station_id: int


class FixtureRequirementCreate(BaseModel):
    customer_id: int
    model_id: int
    station_id: int
    fixture_id: int
    required_qty: int = Field(gt=0)


class FixtureRequirementRead(ORMModel):
    id: int
    model_id: int
    station_id: int
    fixture_id: int
    required_qty: int


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
