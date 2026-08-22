from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import Status, Priority


from enum import Enum


class TaskSortField(str, Enum):
    """Fields available for sorting tasks."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class TaskCreate(BaseModel):
    """Data required to create a task."""

    creator_id: UUID
    title: str
    description: str | None = None
    status: Status = Status.TODO
    priority: Priority = Priority.MEDIUM


class TaskModify(BaseModel):
    """Data to modify a task."""

    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None


class TaskResponse(BaseModel):
    """Response representation for a task."""

    id: UUID
    title: str
    description: str | None
    status: Status
    priority: Priority
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskProjectResponse(BaseModel):
    """Project information icnluded in a detailed task response."""

    id: UUID
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class TaskCreatorResponse(BaseModel):
    """Task creator information included in a detailed task response."""

    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class TaskAssigneeResponse(BaseModel):
    """Assignee information included in a detailed task response."""

    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskResponse):
    """Response representation for a task, including projec,t creator and assignees."""

    project: TaskProjectResponse
    creator: TaskCreatorResponse | None
    assignees: list[TaskAssigneeResponse]


class TaskAssigneeCreate(BaseModel):
    """Data required to add an assignee to a task."""

    username: str
