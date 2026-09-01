from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.common import TimestampedResponse

UserRole = Literal["super_admin", "admin", "user"]


class UserCustomerSummary(BaseModel):
    id: int
    code: str
    name: str


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class UserRead(TimestampedResponse):
    id: int
    username: str
    email: str | None
    display_name: str
    role: str
    is_active: bool
    allowed_customer_ids: list[int]
    allowed_customers: list[UserCustomerSummary] = Field(default_factory=list)


class UserPageRead(BaseModel):
    items: list[UserRead]
    page: int
    page_size: int
    total: int


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    role: UserRole = "user"
    is_active: bool = True
    allowed_customer_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    display_name: str = Field(min_length=1, max_length=120)
    role: UserRole
    is_active: bool = True
    allowed_customer_ids: list[int] | None = None


class UserPasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class OwnPasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ModelShortcutPreferenceRead(BaseModel):
    model_id: int
    model_code: str
    query_count: int
    last_queried_at: datetime | None
    pinned: bool


class ModelShortcutPinUpdate(BaseModel):
    pinned: bool


class AuthSessionRead(BaseModel):
    mode: Literal["user", "guest"]
    user: UserRead | None
    display_name: str
    token: str
    role: str
