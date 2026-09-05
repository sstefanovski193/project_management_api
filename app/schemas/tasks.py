from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.models import Status, Priority


class TaskSortField(str, Enum):
    """Fields available for sorting tasks."""

    TITLE = "title"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class TaskCreate(BaseModel):
    """Data required to create a task."""

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
    project_id: UUID

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


class TaskCommentAuthorResponse(BaseModel):
    """Author information included in a task comment response."""

    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class TaskCommentResponse(BaseModel):
    """Task information included in a detailed task response"""

    id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    author: TaskCommentAuthorResponse | None

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskResponse):
    """Response representation for a task, including project, creator, assignees and comments."""

    project: TaskProjectResponse
    creator: TaskCreatorResponse | None
    assignees: list[TaskAssigneeResponse]
    comments: list[TaskCommentResponse]


class TaskAssigneeCreate(BaseModel):
    """Data required to add an assignee to a task."""

    username: str
