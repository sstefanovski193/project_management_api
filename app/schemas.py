from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models import ApplicationRole, ProjectRole


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


class ProjectCreate(BaseModel):
    name: str
    description: str | None
    creator_id: UUID
    # TODO: remove creator_id once authentication is implemented


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberUserResponse(BaseModel):
    # TODO: add docstrings
    id: UUID
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberResponse(BaseModel):
    # TODO: add docstrings
    role: ProjectRole
    joined_at: datetime
    user: ProjectMemberUserResponse

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    memberships: list[ProjectMemberResponse]
    # TODO: add tasks once task endpoints are implemented


class ProjectSortField(str, Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ProjectMemberCreate(BaseModel):
    user_id: UUID
    role: ProjectRole = ProjectRole.MEMBER
