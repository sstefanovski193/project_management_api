from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi.security import OAuth2PasswordBearer

from app.config import settings

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Hash a plain-text password.

    Args:
        password: Plain-text password to hash.

    Returns:
        The hashed password.
    """
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a password hash.

    Args:
        password: Plain-text password to verify.
        hashed_password: Password hash to verify against.

    Returns:
        True if the password matches the hash otherwise False.
    """
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    """Create JWT access token for a user.

    Args:
        user_id: ID of the user.

    Returns:
        Signed JWT access token.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {"sub": str(user_id), "exp": expires_at}

    return jwt.encode(
        payload=payload, key=settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
