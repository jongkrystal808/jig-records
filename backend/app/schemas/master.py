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
    assigned_user_ids: list[int] = Field(default_factory=list)


class CustomerUpdate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    assigned_user_ids: list[int] = Field(default_factory=list)


class CustomerRead(TimestampedResponse):
    id: int
    code: str
    name: str
    assigned_user_ids: list[int] = Field(default_factory=list)


class FixtureCreate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    responsible_user_id: int | None = None
    line_storage_location: str | None = Field(default=None, max_length=120)
    department_storage_location: str | None = Field(default=None, max_length=120)
    min_stock_qty: int | None = Field(default=None, ge=0)
    description: str | None = None

    _code_validator = field_validator("code")(_validate_fixture_code)


class FixtureUpdate(BaseModel):
    customer_id: int
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    responsible_user_id: int | None = None
    line_storage_location: str | None = Field(default=None, max_length=120)
    department_storage_location: str | None = Field(default=None, max_length=120)
    min_stock_qty: int | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool = True

    _code_validator = field_validator("code")(_validate_fixture_code)


class FixtureRead(TimestampedResponse):
    id: int
    customer_id: int
    responsible_user_id: int | None
    code: str
    name: str
    line_storage_location: str | None
    department_storage_location: str | None
    min_stock_qty: int
    description: str | None
    is_active: bool
    has_image: bool


class FixtureImageUploadRead(BaseModel):
    fixture_id: int
    fixture_code: str
    has_image: bool
    fixture: FixtureRead


class FixtureImageBatchUploadItemRead(BaseModel):
    file_name: str
    fixture_code: str | None = None
    fixture_id: int | None = None
    success: bool
    message: str


class FixtureImageBatchUploadRead(BaseModel):
    requested_count: int
    uploaded_count: int
    failed_count: int
    results: list[FixtureImageBatchUploadItemRead] = Field(default_factory=list)


class FixtureDeleteRead(BaseModel):
    fixture_id: int
    fixture_code: str
    transaction_records_deleted: bool
    transaction_item_count: int
    affected_transaction_count: int
    deleted_transaction_count: int
    deleted_requirement_count: int


class FixtureQualityRowRead(BaseModel):
    fixture_id: int
    fixture_code: str
    fixture_name: str | None
    storage_location: str | None
    min_stock_qty: int
    stock_qty: int
    identifier_stock_qty: int
    related_model_count: int
    has_image: bool
    issue_codes: list[str] = Field(default_factory=list)


class FixtureQualityReportRead(BaseModel):
    total_fixture_count: int
    problematic_fixture_count: int
    missing_name_count: int
    missing_storage_location_count: int
    missing_image_count: int
    missing_min_stock_qty_count: int
    missing_model_relation_count: int
    stock_mismatch_count: int
    rows: list[FixtureQualityRowRead] = Field(default_factory=list)


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


class MachineModelDeleteRead(BaseModel):
    model_id: int
    model_code: str
    deleted_model_station_count: int
    deleted_requirement_count: int
    deleted_capacity_summary_count: int


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


class StationDeleteRead(BaseModel):
    station_id: int
    station_code: str
    deleted_model_station_count: int
    deleted_requirement_count: int
    deleted_capacity_summary_count: int
