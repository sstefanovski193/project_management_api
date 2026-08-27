from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_user_by_id(user_id: UUID, db: Session) -> User | None:
    """Retrieve user by ID.

    Args:
        user_id: ID of the user.
        db: SQLAlchemy database Session.

    Returns:
        User or None.
    """
    user_query = select(User).where(User.id == user_id)

    return db.execute(user_query).scalar_one_or_none()
