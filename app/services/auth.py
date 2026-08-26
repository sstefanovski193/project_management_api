from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.security import verify_password, oauth2_scheme
from app.db.database import get_db
from app.config import settings


def authenticate_user(username: str, password: str, db: Session) -> User | None:
    """Authenticate user with username and password.

    Args:
        username: Username to authenticate.
        password: Password to authenticate.
        db: SQLAlchemy database Session.

    Returns:
        The authenticated user if valid, otherwise None.
    """
    user_query = select(User).where(User.username == username)
    user = db.execute(user_query).scalar_one_or_none()

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Retrieve user represented by an access token.

    Args:
        token: JWT access token. Defaults to Depends(oauth2_scheme).
        db: SQLAlchemy database Session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the token is invalid or the user does not exist.

    Returns:
        The authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            jwt=token, key=settings.jwt_secret_key, algorithms=settings.jwt_algorithm
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = UUID(user_id)

    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user_query = select(User).where(User.id == user_id)
    user = db.execute(user_query).scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
