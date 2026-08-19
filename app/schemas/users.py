from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models import ApplicationRole


class UserSortField(str, Enum):
    """Fields for sorting users."""

    USERNAME = "username"
    EMAIL = "email"
    CREATED_AT = "created_at"


class UserCreate(BaseModel):
    """Data required to create a user."""

    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """Response representation for a user."""

    id: UUID
    username: str
    email: str
    application_role: ApplicationRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
