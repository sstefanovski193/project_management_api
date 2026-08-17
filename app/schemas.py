from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models import ApplicationRole


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    application_role: ApplicationRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class UserSortField(str, Enum):
    USERNAME = "username"
    EMAIL = "email"
    CREATED_AT = "created_at"
