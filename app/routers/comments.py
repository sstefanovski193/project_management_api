from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import Comment, Task, ProjectMember, ProjectRole, User
from app.schemas.comments import CommentData, CommentResponse, CommentResponseDetailed
from app.services.auth import get_current_user
from app.services.comments import (
    get_comment_by_id,
    get_comment_by_id_with_relationships,
)

router = APIRouter(prefix="/comments", tags=["Comments"])
task_comment_router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["Comments"])


@task_comment_router.post("", response_model=CommentResponse)
def create_comment(
    task_id: UUID,
    comment_data: CommentData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a comment.

    Args:
        task_id: ID of the task.
        comment_data: content of the comment.

    Raises:
        HTTPException: If the task is not found.
        HTTPException: If the user is not a member of the project.
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created comment.
    """
    task_query = select(Task).where(Task.id == task_id)
    task = db.execute(task_query).scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task is not found.")

    project_membership_query = select(ProjectMember).where(
        ProjectMember.user_id == current_user.id,
        ProjectMember.project_id == task.project_id,
    )
    project_membership = db.execute(project_membership_query).scalar_one_or_none()

    if project_membership is None:
        raise HTTPException(
            status_code=403, detail="The user is not a member of the project."
        )

    comment = Comment(
        task_id=task_id,
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
    comment_id: UUID,
    comment_data: CommentData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Modify a comment.

    Args:
        comment_id: ID of the comment.
        comment_data: content of the comment.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the user is not the author of the comment.
        HTTPException: If database integrity constraint is violated.

    Returns:
        The modified comment.
    """
    comment = get_comment_by_id(comment_id, db)

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="The user is not the author of the comment."
        )

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
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a comment.

    Args:
        comment_id: ID of the comment.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the user is not the owner of the comment.
        HTTPException: If the user is not the manager of the project.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    comment = get_comment_by_id_with_relationships(comment_id, db)

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    project_ownership_query = select(ProjectMember).where(
        ProjectMember.user_id == current_user.id,
        ProjectMember.project_id == comment.task.project_id,
        ProjectMember.role == ProjectRole.MANAGER,
    )
    project_ownership = (
        db.execute(project_ownership_query).scalar_one_or_none() is not None
    )
    is_author = comment.user_id == current_user.id

    if not is_author and not project_ownership:
        raise HTTPException(
            status_code=403, detail="The user is not permitted to delete the comment."
        )

    try:
        db.delete(comment)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Success"}


@router.get("/{comment_id}", response_model=CommentResponseDetailed)
def get_comment(comment_id: UUID, db: Session = Depends(get_db)):
    """Retrieve comment

    Args:
        comment_id: ID of the comment.

    Raises:
        HTTPException: If the comment is not found.

    Returns:
        The requested comment.
    """

    comment = get_comment_by_id_with_relationships(comment_id, db)

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    return comment
