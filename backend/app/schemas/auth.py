from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.common import TimestampedResponse


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class UserRead(TimestampedResponse):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    role: str = Field(default="user", min_length=1, max_length=32)
    is_active: bool = True


class UserUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=32)
    is_active: bool = True


class UserPasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class AuthSessionRead(BaseModel):
    mode: Literal["user", "guest"]
    user: UserRead | None
    display_name: str
    token: str
    role: str
