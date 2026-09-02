from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Task, Comment, TaskAssignee


def get_task_by_id(task_id: UUID, db: Session) -> Task | None:
    """Retrieve task by ID.

    Args:
        task_id: ID of the task.
        db: SQLAlchemy database Session.

    Returns:
        Task instance or None.
    """
    task_query = select(Task).where(Task.id == task_id)
    task = db.execute(task_query).scalar_one_or_none()

    return task


def get_task_by_id_with_relationships(task_id: UUID, db: Session) -> Task | None:
    """Retrieve task by ID with related project, creator, assignees and comments loaded.

    Args:
        task_id: ID of the task.
        db: SQLAlchemy database Session.

    Returns:
        Task instance or None.
    """
    task_query = (
        select(Task)
        .where(Task.id == task_id)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees),
            selectinload(Task.comments).selectinload(Comment.author),
        )
    )
    task = db.execute(task_query).scalar_one_or_none()

    return task


def get_task_assignee(task_id: UUID, user_id: UUID, db: Session) -> TaskAssignee | None:
    """Retrieve task assignee.

    Args:
        task_id: ID of the task.
        user_id: ID of the user.
        db: SQLAlchemy database Session.

    Returns:
        Task assignee if found, otherwise None.
    """
    task_assignee_query = select(TaskAssignee).where(
        TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id
    )

    return db.execute(task_assignee_query).scalar_one_or_none()
