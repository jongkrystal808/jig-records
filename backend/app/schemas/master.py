from pydantic import BaseModel, Field

from backend.app.schemas.common import TimestampedResponse


class CustomerCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)


class CustomerRead(TimestampedResponse):
    id: int
    code: str
    name: str


class FixtureCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class FixtureRead(TimestampedResponse):
    id: int
    code: str
    name: str
    description: str | None
    is_active: bool


class MachineModelCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)


class MachineModelRead(TimestampedResponse):
    id: int
    code: str
    name: str


class StationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)


class StationRead(TimestampedResponse):
    id: int
    code: str
    name: str


class OwnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class OwnerRead(TimestampedResponse):
    id: int
    name: str
