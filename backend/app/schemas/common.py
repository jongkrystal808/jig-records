from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda value: value.date().isoformat()},
    )


class TimestampedResponse(ORMModel):
    created_at: datetime
    updated_at: datetime


class CsvImportPayload(BaseModel):
    filename: str | None = None
    content: str = Field(min_length=1)


class ImportResultRead(BaseModel):
    imported_count: int
