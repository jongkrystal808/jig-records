from pydantic import BaseModel, Field

from backend.app.schemas.common import ORMModel


class FixtureRequirementCreate(BaseModel):
    station_id: int
    fixture_id: int
    required_qty: int = Field(gt=0)


class FixtureRequirementRead(ORMModel):
    id: int
    station_id: int
    fixture_id: int
    required_qty: int


class CapacityRead(ORMModel):
    station_id: int
    station_code: str
    station_name: str
    max_open_station_count: int
    bottleneck_fixture_code: str | None
