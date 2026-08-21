from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from app.models import Status, Priority


class TaskCreate(BaseModel):
    """Data required to create a task."""

    creator_id: UUID
    title: str
    description: str | None = None
    status: Status = Status.TODO
    priority: Priority = Priority.MEDIUM


class TaskResponse(BaseModel):
    """Response representation for a task."""

    id: UUID
    title: str
    description: str | None
    status: Status
    priority: Priority
    created_at: datetime
    updated_at: datetime


class TaskProjectResponse(BaseModel):
    """Project information icnluded in a detailed task response."""

    id: UUID
    name: str
    description: str | None


class TaskCreatorResponse(BaseModel):
    """Task creator information included in a detailed task response."""

    id: UUID
    username: str


class TaskAssigneeResponse(BaseModel):
    """Assignee information included in a detailed task response."""

    id: UUID
    username: str


class TaskDetailResponse(TaskResponse):
    """Response representation for a task, including projec,t creator and assignees."""

    project: TaskProjectResponse
    creator: TaskCreatorResponse
    assignees: list[TaskAssigneeResponse] | None


class TaskAssigneeCreate(BaseModel):
    """Data required to add an assignee to a task."""

    username: str
