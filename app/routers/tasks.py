from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import (
    Task,
    Project,
    User,
    ProjectMember,
    TaskAssignee,
    Status,
    Priority,
)
from app.schemas.tasks import (
    TaskCreate,
    TaskResponse,
    TaskDetailResponse,
    TaskAssigneeCreate,
    TaskSortField,
)
from app.schemas.common import SortOrder
from app.services.tasks import (
    get_task_by_id,
    get_task_by_id_with_relationships,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])
project_task_router = APIRouter(prefix="/projects/{task_id}/tasks", tags=["Tasks"])


@project_task_router.post("", response_model=TaskResponse)
def create_task(project_id: UUID, task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a task.

    Args:
        project_id: ID of the project.
        task_data: creator_id, title, description, status and priority.

    Raises:
        HTTPException: If the project is not found.
        HTTPException: if the user is not found.
        HTTPException: If the user is not a member of the project.
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created task.
    """
    # TODO: update creator_id once authentication is implemented
    project_query = select(Project).where(Project.id == project_id)
    project = db.execute(project_query).scalar_one_or_none()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    user_query = select(User).where(User.id == task_data.creator_id)
    user = db.execute(user_query).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    project_membership_query = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == task_data.creator_id,
    )
    project_membership = db.execute(project_membership_query).scalar_one_or_none()

    if project_membership is None:
        raise HTTPException(
            status_code=403, detail="The user is not member of the project."
        )

    task = Task(
        project_id=project_id,
        creator_id=task_data.creator_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
    )

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return task


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get task by ID.

    Args:
        task_id: ID of the task.

    Raises:
        HTTPException: If task is not found.

    Returns:
        The requested task
    """

    task = get_task_by_id_with_relationships(task_id, db)

    if task is None:
        raise HTTPException(status_code=404, detail="Task is not found.")

    return task


@router.get("", response_model=list[TaskResponse])
def get_tasks(
    username: str | None = None,
    project_name: str | None = None,
    status: Status | None = None,
    priority: Priority | None = None,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: TaskSortField = TaskSortField.CREATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    db: Session = Depends(get_db),
):
    """Retrieve Tasks

    Args:
        username: Username of an assignee. Defaults to None.
        project_name: Project name. Defaults to None.
        status: Status of the task. Defaults to None.
        priority: Priority of the task. Defaults to None.
        sort_by: Sort order by CREATED_AT or UPDATED_AT. Defaults to TaskSortField.CREATED_AT.
        sort_order: Sort order by asc or desc. Defaults to SortOrder.DESC.

    Returns:
        A list of tasks.
    """
    task_query = select(Task)

    if status is not None:
        task_query = task_query.where(Task.status == status)

    if priority is not None:
        task_query = task_query.where(Task.priority == priority)

    if project_name is not None:
        task_query = task_query.where(Task.project.has(Project.name == project_name))

    if username is not None:
        task_query = task_query.where(Task.assignees.any(User.username == username))

    sort_columns = {
        TaskSortField.CREATED_AT: Task.created_at,
        TaskSortField.UPDATED_AT: Task.updated_at,
    }
    sort_column = sort_columns[sort_by]

    if sort_order == SortOrder.ASC:
        task_query = task_query.order_by(sort_column.asc())
    else:
        task_query = task_query.order_by(sort_column.desc())

    task_query = task_query.offset(offset).limit(limit)
    tasks = db.execute(task_query).scalars().all()

    return tasks


@router.post("/{task_id}/assignees")
def add_task_assignee(
    task_id: UUID,
    assignee_data: TaskAssigneeCreate,
    db: Session = Depends(get_db),
):
    """Add an assignee to a task.

    Args:
        task_id: ID of the task.
        assignee_data: username of the assignee(user).

    Raises:
        HTTPException: If the task is not found.
        HTTPException: If the user is not found.
        HTTPException: If the user is not a member of the project.
        HTTPException: If the user is already assigned to the task.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    task = get_task_by_id(task_id, db)
    if task is None:
        raise HTTPException(status_code=404, detail="Task is not found.")

    user_query = select(User).where(User.username == assignee_data.username)
    user = db.execute(user_query).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    project_member_query = select(ProjectMember).where(
        ProjectMember.user_id == user.id, ProjectMember.project_id == task.project_id
    )
    project_member = db.execute(project_member_query).scalar_one_or_none()

    if project_member is None:
        raise HTTPException(
            status_code=403, detail="The user is not a member of the project."
        )

    task_assignee_query = select(TaskAssignee).where(
        TaskAssignee.task_id == task_id, TaskAssignee.user_id == user.id
    )
    task_assignee = db.execute(task_assignee_query).scalar_one_or_none()

    if task_assignee:
        raise HTTPException(
            status_code=409, detail="The user is already assigned to the task."
        )

    task_assignee = TaskAssignee(task_id=task_id, user_id=user.id)

    try:
        db.add(task_assignee)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Success"}


@router.delete("/{task_id}/assignees/{user_id}")
def delete_task_assignee(task_id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    """Delete an assignee from a task.

    Args:
        task_id: ID of the task.
        user_id: ID of the user.

    Raises:
        HTTPException: If the task is not found.
        HTTPException: If the user is not assigned to the task.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    task = get_task_by_id(task_id, db)
    if task is None:
        raise HTTPException(status_code=404, detail="Task is not found.")

    task_assignee_query = select(TaskAssignee).where(
        TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id
    )
    task_assignee = db.execute(task_assignee_query).scalar_one_or_none()

    if task_assignee is None:
        raise HTTPException(
            status_code=404, detail="The user is not assigned to the task."
        )

    try:
        db.delete(task_assignee)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Assignee successfully removed"}
