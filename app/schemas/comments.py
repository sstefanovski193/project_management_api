from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import Status, Priority


class CommentCreate(BaseModel):
    """Data required to create a comment."""

    # TODO: update once authentication is implemented
    user_id: UUID
    content: str


class CommentModify(BaseModel):
    """Data required to modify a comment."""

    content: str
    user_id: UUID


class CommentResponse(BaseModel):
    """Response representation for a comment."""

    id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentTaskResponse(BaseModel):
    """Task information included in a detailed comment response."""

    id: UUID
    title: str
    description: str | None
    status: Status
    priority: Priority
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentAuthorResponse(BaseModel):
    """Author information included in a detailed comment response."""

    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class CommentResponseDetailed(CommentResponse):
    """Detailed response representation for a comment."""

    task_id: UUID
    updated_at: datetime
    task: CommentTaskResponse
    author: CommentAuthorResponse | None
