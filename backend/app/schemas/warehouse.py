from pydantic import BaseModel, Field

from backend.app.schemas.common import TimestampedResponse


class StorageLocationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    area: str = Field(min_length=1, max_length=8)
    rack: str = Field(min_length=1, max_length=8)
    layer: str = Field(min_length=1, max_length=8)
    description: str | None = None
    image_path: str | None = None


class StorageLocationRead(TimestampedResponse):
    id: int
    code: str
    area: str
    rack: str
    layer: str
    description: str | None
    image_path: str | None


class FixtureLocationAssignmentCreate(BaseModel):
    fixture_id: int
    location_id: int


class FixtureLocationAssignmentRead(TimestampedResponse):
    id: int
    fixture_id: int
    location_id: int


class FixtureImageCreate(BaseModel):
    fixture_id: int
    image_path: str = Field(min_length=1, max_length=255)
    thumbnail_path: str | None = Field(default=None, max_length=255)
    is_main: bool = False


class FixtureImageRead(TimestampedResponse):
    id: int
    fixture_id: int
    image_path: str
    thumbnail_path: str | None
    is_main: bool
