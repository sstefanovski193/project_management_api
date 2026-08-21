from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Task


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
    """Retrieve task by ID with related project, creator, and assignees loaded.

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
        )
    )
    task = db.execute(task_query).scalar_one_or_none()

    return task
