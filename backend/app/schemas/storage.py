from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.schemas.common import TimestampedResponse


class StorageContainerCreate(BaseModel):
    customer_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=255)


class StorageContainerUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=255)


class StorageContainerRead(TimestampedResponse):
    id: int
    customer_id: int
    name: str
    description: str | None
    code_count: int = 0
    fixture_type_count: int = 0
    total_quantity: int = 0
    pending_quantity_count: int = 0


class StorageCodeRead(TimestampedResponse):
    id: int
    customer_id: int
    container_id: int | None
    container_name: str | None
    code: str
    is_active: bool
    fixture_type_count: int = 0
    total_quantity: int = 0
    pending_quantity_count: int = 0


class StorageCodeOrganize(BaseModel):
    customer_id: int
    storage_code_ids: list[int] = Field(min_length=1)
    container_id: int | None = None


class StorageCodeRegister(BaseModel):
    customer_id: int
    location_text: str = Field(min_length=1, max_length=1000)


class StorageStationOption(BaseModel):
    model_id: int
    model_code: str
    model_name: str
    station_id: int
    station_code: str
    station_name: str


class FixturePlacementInput(BaseModel):
    target_type: Literal["storage_code", "model_station"]
    storage_code_id: int | None = None
    model_id: int | None = None
    station_id: int | None = None
    quantity: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_target(self):
        if self.target_type == "storage_code":
            if self.storage_code_id is None or self.model_id is not None or self.station_id is not None:
                raise ValueError("storage_code target requires storage_code_id only")
        elif self.storage_code_id is not None or self.model_id is None or self.station_id is None:
            raise ValueError("model_station target requires model_id and station_id only")
        return self


class FixturePlacementUpdate(BaseModel):
    placements: list[FixturePlacementInput] = Field(default_factory=list)


class FixturePlacementRead(TimestampedResponse):
    id: int
    fixture_id: int
    target_type: Literal["storage_code", "model_station"]
    storage_code_id: int | None
    storage_code: str | None
    container_id: int | None
    container_name: str | None
    model_id: int | None
    model_code: str | None
    model_name: str | None
    station_id: int | None
    station_code: str | None
    station_name: str | None
    quantity: int | None
    source: str
    display_label: str


class FixturePlacementDetail(BaseModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str
    customer_id: int
    stock_qty: int
    allocated_qty: int
    unallocated_qty: int
    has_pending_quantities: bool
    placements: list[FixturePlacementRead]
    station_options: list[StorageStationOption]


class StorageOverviewRead(BaseModel):
    customer_id: int
    containers: list[StorageContainerRead]
    codes: list[StorageCodeRead]
    ungrouped_code_count: int
    pending_quantity_count: int
