from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models import ProjectRole

# TODO: Add Field description for the Swagger UI docs


class ProjectSortField(str, Enum):
    """Fields for sorting projects."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ProjectCreate(BaseModel):
    """Data required to create a project."""

    name: str
    description: str | None
    creator_id: UUID
    # TODO: remove creator_id once authentication is implemented


class ProjectResponse(BaseModel):
    """Response representation for a project."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberUserResponse(BaseModel):
    """User information included in a project membership response."""

    id: UUID
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberResponse(BaseModel):
    """Response representation of a project membership."""

    role: ProjectRole
    joined_at: datetime
    user: ProjectMemberUserResponse

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Response representation for a project, including memberships and tasks."""

    memberships: list[ProjectMemberResponse]
    # TODO: add tasks once task endpoints are implemented


class ProjectMemberCreate(BaseModel):
    """Data required to add a member to a project."""

    user_id: UUID
    role: ProjectRole = ProjectRole.MEMBER
