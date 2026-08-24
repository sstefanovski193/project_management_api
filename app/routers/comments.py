from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import Comment, Task, ProjectMember, ProjectRole
from app.schemas.comments import (
    CommentCreate,
    CommentResponse,
    CommentModify,
    CommentResponseDetailed,
)
from app.services.comments import (
    get_comment_by_id,
    get_comment_by_id_with_relationships,
)

router = APIRouter(prefix="/comments", tags=["Comments"])
task_comment_router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["Comments"])


@task_comment_router.post("", response_model=CommentResponse)
def create_comment(
    task_id: UUID, comment_data: CommentCreate, db: Session = Depends(get_db)
):
    """Create a comment.

    Args:
        task_id: ID of the task.
        comment_data: user_id of the author and content of the comment.

    Raises:
        HTTPException: If the task is not found.
        HTTPException: If the user is not a member of the project.
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created comment.
    """
    comment = Comment(
        task_id=task_id,
        user_id=comment_data.user_id,
        content=comment_data.content,
    )

    task_query = select(Task).where(Task.id == task_id)
    task = db.execute(task_query).scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task is not found.")

    project_membership_query = select(ProjectMember).where(
        ProjectMember.user_id == comment_data.user_id,
        ProjectMember.project_id == task.project_id,
    )
    project_membership = db.execute(project_membership_query).scalar_one_or_none()

    if project_membership is None:
        raise HTTPException(
            status_code=403, detail="The user is not a member of the project."
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
    comment_id: UUID, comment_data: CommentModify, db: Session = Depends(get_db)
):
    """Modify a comment.

    Args:
        comment_id: ID of the comment.
        comment_data: user_id of the requestor and content of the comment.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the user is not the author of the comment.
        HTTPException: If database integrity constraint is violated.

    Returns:
        The modified comment.
    """
    # TODO: update once authentication is implemented
    comment = get_comment_by_id(comment_id, db)

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    if comment.user_id != comment_data.user_id:
        raise HTTPException(
            status_code=403, detail="The user is not the author of the comment."
        )

    try:
        comment.content = comment_data.content
        comment.updated_at = datetime.now(timezone.utc)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    db.refresh(comment)
    return comment


@router.delete("/{comment_id}")
def delete_comment(comment_id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    """Delete a comment.

    Args:
        comment_id: ID of the comment.
        user_id: User id of the requestor.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the user is not the owner of the comment.
        HTTPException: If the user is not the manager of the project.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    # TODO: update once authorization is implemented
    comment = get_comment_by_id_with_relationships(comment_id, db)

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    project_ownership_query = select(ProjectMember).where(
        ProjectMember.user_id == user_id,
        ProjectMember.project_id == comment.task.project_id,
        ProjectMember.role == ProjectRole.MANAGER,
    )
    project_ownership = db.execute(project_ownership_query).scalar_one_or_none()

    if project_ownership is None:
        if comment.author:
            if comment.author.id != user_id:
                raise HTTPException(
                    status_code=409, detail="User is not the owner of the comment."
                )
        else:
            raise HTTPException(
                status_code=409,
                detail="User is not the manager of the project.",
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
