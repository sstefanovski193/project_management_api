from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import User, Project, ProjectMember, ProjectRole
from app.schemas.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectSortField,
    ProjectMemberCreate,
    ProjectMemberResponse,
)
from app.schemas.common import SortOrder

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    # TODO: update once authentication is implemented
    user_query = select(User).where(User.id == project_data.creator_id)
    creator = db.execute(user_query).scalar_one_or_none()

    if creator is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    project = Project(name=project_data.name, description=project_data.description)

    try:
        db.add(project)
        db.flush()

        project_member = ProjectMember(
            user_id=project_data.creator_id,
            project_id=project.id,
            role=ProjectRole.MANAGER,
        )

        db.add(project_member)
        db.commit()
        db.refresh(project)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return project


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    project_id: UUID, project_member: ProjectMemberCreate, db: Session = Depends(get_db)
):
    member_query = select(User).where(User.id == project_member.user_id)
    member = db.execute(member_query).scalar_one_or_none()

    if member is None:
        raise HTTPException(status_code=404, detail="User not found")

    project_query = select(Project).where(Project.id == project_id)
    project = db.execute(project_query).scalar_one_or_none()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    membership_query = select(ProjectMember).where(
        ProjectMember.user_id == project_member.user_id,
        ProjectMember.project_id == project_id,
    )

    existing_membership = db.execute(membership_query).scalar_one_or_none()
    if existing_membership:
        raise HTTPException(
            status_code=409, detail="The user is already a member of this project"
        )

    new_membership = ProjectMember(
        user_id=project_member.user_id, project_id=project_id, role=ProjectRole.MEMBER
    )

    try:
        db.add(new_membership)
        db.commit()
        db.refresh(new_membership)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not add project member")

    return new_membership


@router.delete("/{project_id}/members/{user_id}")
def delete_project_member(
    project_id: UUID, user_id: UUID, db: Session = Depends(get_db)
):
    query = select(ProjectMember).where(
        ProjectMember.user_id == user_id, ProjectMember.project_id == project_id
    )
    existing_membership = db.execute(query).scalar_one_or_none()

    if existing_membership is None:
        raise HTTPException(status_code=404, detail="Project membership not found")

    db.delete(existing_membership)
    db.commit()

    return {"message": "Project member removed successfully"}


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    query = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.memberships).selectinload(ProjectMember.user))
    )
    project = db.execute(query).scalar_one_or_none()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.get("", response_model=list[ProjectResponse])
def get_projects(
    limit: int = Query(default=50, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    sort_by: ProjectSortField = ProjectSortField.CREATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    db: Session = Depends(get_db),
):
    # TODO: add filtering use cases for get projects

    sort_columns = {
        ProjectSortField.NAME: Project.name,
        ProjectSortField.CREATED_AT: Project.created_at,
        ProjectSortField.UPDATED_AT: Project.updated_at,
    }
    sort_column = sort_columns[sort_by]

    query = select(Project)

    if sort_order == SortOrder.ASC:
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.limit(limit).offset(offset)
    projects = db.execute(query).scalars().all()

    return projects
