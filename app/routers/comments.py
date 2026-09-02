from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import Comment, Task, ProjectMember, User
from app.schemas.comments import CommentData, CommentResponse, CommentResponseDetailed
from app.services.auth import get_current_user
from app.dependencies.authorization import (
    require_comment_author,
    require_comment_delete_rights,
    require_comment_project_member,
    require_task_project_member,
)

router = APIRouter(prefix="/comments", tags=["Comments"])
task_comment_router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["Comments"])


@task_comment_router.post("", response_model=CommentResponse)
def create_comment(
    comment_data: CommentData,
    task: Task = Depends(require_task_project_member),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a comment.

    Only project members can create comments on a task.

    Args:
        comment_data: content of the comment.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created comment.
    """
    comment = Comment(
        task_id=task.id,
        user_id=current_user.id,
        content=comment_data.content,
    )

    try:
        db.add(comment)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    db.refresh(comment)

    return comment


@router.patch("/{comment_id}", response_model=CommentResponse)
def modify_comment(
    comment_data: CommentData,
    comment: Comment = Depends(require_comment_author),
    db: Session = Depends(get_db),
):
    """Modify a comment.

    Only the comment author can modify a comment.

    Args:
        comment_data: content of the comment.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        The modified comment.
    """
    comment.content = comment_data.content
    comment.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    db.refresh(comment)
    return comment


@router.delete("/{comment_id}")
def delete_comment(
    comment: Comment = Depends(require_comment_delete_rights),
    db: Session = Depends(get_db),
):
    """Delete a comment.

    Only comment author or project manager can delete a comment.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    try:
        db.delete(comment)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Success"}


@router.get("/{comment_id}", response_model=CommentResponseDetailed)
def get_comment(comment: Comment = Depends(require_comment_project_member)):
    """Retrieve comment.

    The authenticated user must be member of the comment's project.

    Returns:
        The requested comment.
    """
    return comment
