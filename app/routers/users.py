from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import User, ApplicationRole
from app.schemas.users import UserCreate, UserResponse, UserSortField
from app.schemas.common import SortOrder
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        application_role=ApplicationRole.USER,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists")

    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    query = select(User).where(User.id == user_id)
    user = db.execute(query).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("", response_model=list[UserResponse])
def get_users(
    limit: int = Query(default=50, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    sort_by: UserSortField = UserSortField.CREATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    application_role: ApplicationRole | None = None,
    db: Session = Depends(get_db),
):
    sort_columns = {
        UserSortField.USERNAME: User.username,
        UserSortField.EMAIL: User.email,
        UserSortField.CREATED_AT: User.created_at,
    }
    sort_column = sort_columns[sort_by]

    query = select(User)

    if application_role is not None:
        query = query.where(User.application_role == application_role)

    if sort_order == SortOrder.ASC:
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.offset(offset).limit(limit)
    users = db.execute(query).scalars().all()

    return users
