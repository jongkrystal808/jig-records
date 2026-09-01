from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json", check_fields=False)
    def serialize_business_dates(self, value):
        if isinstance(value, datetime):
            return value.date().isoformat()
        return value


class TimestampedResponse(ORMModel):
    created_at: datetime
    updated_at: datetime


class CsvImportPayload(BaseModel):
    filename: str | None = None
    content: str = Field(min_length=1)


class ImportResultRead(BaseModel):
    imported_count: int
