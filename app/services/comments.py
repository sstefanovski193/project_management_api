from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Comment


def get_comment_by_id(comment_id: UUID, db: Session) -> Comment | None:
    """Retrieve comment by ID.

    Args:
        comment_id: ID of the comment.
        db: SQLAlchemy database Session.

    Returns:
        Comment instance or None.
    """
    comment_query = select(Comment).where(Comment.id == comment_id)
    comment = db.execute(comment_query).scalar_one_or_none()

    return comment


def get_comment_by_id_with_relationships(
    comment_id: UUID, db: Session
) -> Comment | None:
    """Retrieve comment by ID and eagerly load task and author.

    Args:
        comment_id: ID of the comment.
        db: SQLAlchemy database Session.

    Returns:
        Comment instance or None.
    """
    comment_query = (
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.task), selectinload(Comment.author))
    )
    comment = db.execute(comment_query).scalar_one_or_none()

    return comment
