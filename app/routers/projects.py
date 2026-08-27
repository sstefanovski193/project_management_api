from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.services.auth import get_current_user
from app.models import User, Project, ProjectMember, ProjectRole, Task
from app.schemas.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectSortField,
    ProjectMemberCreate,
    ProjectMemberResponse,
)
from app.schemas.common import SortOrder
from app.services.projects import get_project_by_id, get_project_membership
from app.services.users import get_user_by_id
from app.dependencies.authorization import require_admin, require_project_manager

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a project.

    Args:
        project_data: Name, description of the project.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created project.
    """
    project = Project(name=project_data.name, description=project_data.description)

    try:
        db.add(project)
        db.flush()

        project_member = ProjectMember(
            user_id=current_user.id,
            project_id=project.id,
            role=ProjectRole.MANAGER,
        )

        db.add(project_member)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    db.refresh(project)

    return project


@router.delete("/{project_id}", dependencies=[Depends(require_admin)])
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    """Delete project.

    Only application administrators can delete projects.

    Args:
        project_id: ID of the project.

    Raises:
        HTTPException: If the project is not found.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    project = get_project_by_id(project_id, db)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    task_query = select(Task).where(Task.project_id == project_id).limit(1)
    task = db.execute(task_query).scalar_one_or_none()

    if task is not None:
        raise HTTPException(
            status_code=409, detail="Project cannot be deleted while it contains tasks."
        )

    try:
        db.delete(project)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Success"}


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    dependencies=[Depends(require_project_manager)],
)
def add_project_member(
    project_id: UUID, project_member: ProjectMemberCreate, db: Session = Depends(get_db)
):
    """Add a member to a project.

    Only project managers can add project members.

    Args:
        project_id: Project.id
        project_member: user_id and ProjectRole.MEMBER.

    Raises:
        HTTPException: If user is not found.
        HTTPException: If the user is already a member of the project.
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created project membership.
    """
    user = get_user_by_id(project_member.user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    existing_membership = get_project_membership(project_member.user_id, project_id, db)
    if existing_membership is not None:
        raise HTTPException(
            status_code=409, detail="The user is already a member of this project"
        )

    new_membership = ProjectMember(
        user_id=project_member.user_id, project_id=project_id, role=project_member.role
    )

    try:
        db.add(new_membership)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not add project member")

    db.refresh(new_membership)

    return new_membership


@router.delete(
    "/{project_id}/members/{user_id}", dependencies=[Depends(require_project_manager)]
)
def delete_project_member(
    project_id: UUID, user_id: UUID, db: Session = Depends(get_db)
):
    """Delete a member from a project.

    Only project managers can delete project members.

    Args:
        project_id: ID of the project.
        user_id: ID of the user.

    Raises:
        HTTPException: If project membership is not found.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    existing_membership = get_project_membership(user_id, project_id, db)
    if existing_membership is None:
        raise HTTPException(status_code=404, detail="Project membership not found")

    try:
        db.delete(existing_membership)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Project member removed successfully"}


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get project by ID.

    Args:
        project_id: ID of the project.

    Raises:
        HTTPException: If the project is not found.

    Returns:
        The requested project.
    """
    query = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.memberships).selectinload(ProjectMember.user),
            selectinload(Project.tasks),
        )
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
    """Get projects.

    Args:
        sort_by: Sort by NAME, CREATED_AT or UPDATED_AT. Defaults to ProjectSortField.CREATED_AT.
        sort_order: Sort order by asc or desc. Defaults to SortOrder.DESC.

    Returns:
        A list of projects.
    """
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
