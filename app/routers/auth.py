from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import TokenResponse
from app.services.auth import authenticate_user, get_current_user
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate a user

    Args:
        form_data: User login credentials.

    Raises:
        HTTPException: If the username or password is invalid.

    Returns:
        Access token for the authenticated user.
    """
    user = authenticate_user(
        username=form_data.username, password=form_data.password, db=db
    )

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(user.id)

    return {"access_token": access_token, "token_type": "bearer"}
