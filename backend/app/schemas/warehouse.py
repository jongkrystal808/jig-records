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
