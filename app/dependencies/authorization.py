from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import ApplicationRole, User, Task, Comment
from app.services.auth import get_current_user
from app.services.projects import (
    is_project_manager,
    get_project_membership,
    get_project_by_id,
)
from app.services.tasks import get_task_by_id, get_task_by_id_with_relationships
from app.services.comments import (
    get_comment_by_id,
    get_comment_by_id_with_relationships,
)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated current user to have admin application role.

    Raises:
        HTTPException: If the authenticated user is not an application admin.

    Returns:
        The authenticated user.
    """
    if current_user.application_role != ApplicationRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin rights required.")

    return current_user


def require_project_manager(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Require the authenticated current user to have manager project role.

    Args:
        project_id: ID of the project.

    Raises:
        HTTPException: If the project is not found.
        HTTPException: If the authenticated user is not a project manager.

    Returns:
        The authenticated user.
    """
    project = get_project_by_id(project_id, db)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not is_project_manager(current_user.id, project_id, db):
        raise HTTPException(status_code=403, detail="Project manager rights required.")

    return current_user


def require_project_member(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Require the authenticated current user to be project member.

    Args:
        project_id: ID of the project

    Raises:
        HTTPException: If the project is not found.
        HTTPException: If the authenticated user is not a project member.

    Returns:
        The authenticated user.
    """
    project = get_project_by_id(project_id, db)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    membership = get_project_membership(current_user.id, project_id, db)
    if membership is None:
        raise HTTPException(
            status_code=403, detail="Project membership rights required."
        )

    return current_user


def require_task_project_member(
    task_id: UUID,
    current_user: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    """Require the authenticated current user to be member of the task's project.

    Args:
        task_id: ID of the task.

    Raises:
        HTTPException: If the task is not found.
        HTTPException: If the authenticated user is not a project member.

    Returns:
        The requested task.
    """
    task = get_task_by_id(task_id, db)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    project_membership = get_project_membership(current_user.id, task.project_id, db)
    if project_membership is None:
        raise HTTPException(
            status_code=403, detail="Project membership rights required."
        )

    return task


def require_task_project_member_with_relationships(
    task_id: UUID,
    current_user: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    """Require the authenticated current user to be member of the task's project.

    Args:
        task_id: ID of the task.

    Raises:
        HTTPException: If the task is not found.
        HTTPException: If the authenticated user is not a project member.

    Returns:
        The requested task, including relationships eagerly loaded.
    """
    task = get_task_by_id_with_relationships(task_id, db)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    project_membership = get_project_membership(current_user.id, task.project_id, db)
    if project_membership is None:
        raise HTTPException(
            status_code=403, detail="Project membership rights required."
        )

    return task


def require_comment_author(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    """Require the authenticated current user to be the comment author.

    Args:
        comment_id: ID of the comment.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the authenticated user is not the comment author.

    Returns:
        The requested comment.
    """
    comment = get_comment_by_id(comment_id, db)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Comment author rights required.")

    return comment


def require_comment_delete_rights(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    """Require permission to delete a comment.

    Args:
        comment_id: ID of the comment.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the authenticated user is not permitted to delete the comment.

    Returns:
        The requested comment.
    """
    comment = get_comment_by_id_with_relationships(comment_id, db)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    is_author = comment.user_id == current_user.id
    is_manager = is_project_manager(current_user.id, comment.task.project_id, db)

    if not is_author and not is_manager:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete the comment."
        )

    return comment


def require_comment_project_member(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    """Require the authenticated current user to belong to the comment's project.

    Args:
        comment_id: ID of the comment.

    Raises:
        HTTPException: If the comment is not found.
        HTTPException: If the authenticated user is not a project member.

    Returns:
        The requested comment.
    """
    comment = get_comment_by_id_with_relationships(comment_id, db)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")

    project_membership = get_project_membership(
        current_user.id, comment.task.project_id, db
    )
    if project_membership is None:
        raise HTTPException(
            status_code=403, detail="Project membership rights required."
        )

    return comment
