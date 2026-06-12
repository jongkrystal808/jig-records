from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import TimestampedResponse


def _validate_fixture_code(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("治具編號不可為空")
    return stripped


class CustomerCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)


class CustomerRead(TimestampedResponse):
    id: int
    code: str
    name: str


class FixtureCreate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    manage_type: Literal["datecode", "serial"] = "datecode"
    owner_id: int | None = None
    storage_location: str | None = Field(default=None, max_length=120)
    min_stock_qty: int | None = Field(default=None, ge=0)
    description: str | None = None

    _code_validator = field_validator("code")(_validate_fixture_code)


class FixtureUpdate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    manage_type: Literal["datecode", "serial"] = "datecode"
    owner_id: int | None = None
    storage_location: str | None = Field(default=None, max_length=120)
    min_stock_qty: int | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool = True

    _code_validator = field_validator("code")(_validate_fixture_code)


class FixtureRead(TimestampedResponse):
    id: int
    customer_id: int
    owner_id: int | None
    code: str
    name: str
    manage_type: Literal["datecode", "serial"]
    storage_location: str | None
    min_stock_qty: int
    description: str | None
    is_active: bool


class MachineModelCreate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)


class MachineModelUpdate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    is_active: bool = True


class MachineModelRead(TimestampedResponse):
    id: int
    customer_id: int
    code: str
    name: str
    is_active: bool


class StationCreate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)


class StationUpdate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    is_active: bool = True


class StationRead(TimestampedResponse):
    id: int
    customer_id: int
    code: str
    name: str
    is_active: bool


class OwnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class OwnerUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    is_active: bool = True


class OwnerRead(TimestampedResponse):
    id: int
    name: str
    is_active: bool
