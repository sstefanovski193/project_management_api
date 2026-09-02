from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import (
    Task,
    Project,
    User,
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
    TaskModify,
)
from app.schemas.common import SortOrder
from app.dependencies.authorization import (
    require_project_member,
    require_task_project_member,
    require_task_project_member_with_relationships,
)
from app.services.auth import get_current_user
from app.services.projects import get_project_membership
from app.services.tasks import get_task_assignee

router = APIRouter(prefix="/tasks", tags=["Tasks"])
project_task_router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@project_task_router.post("", response_model=TaskResponse)
def create_task(
    project_id: UUID,
    task_data: TaskCreate,
    current_user: User = Depends(require_project_member),
    db: Session = Depends(get_db),
):
    """Create a task.

    Only project members can create a new task within a project.

    Args:
        project_id: ID of the project.
        task_data: title, description, status and priority of the task.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        The created task.
    """
    task = Task(
        project_id=project_id,
        creator_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
    )

    try:
        db.add(task)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    db.refresh(task)

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def modify_task(
    task_modify_data: TaskModify,
    task: Task = Depends(require_task_project_member),
    db: Session = Depends(get_db),
):
    """Modify a task.

    Only project members can modify a task.

    Args:
        task_modify_data: title, description, status and priority.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        The modified task.
    """
    modify_data = task_modify_data.model_dump(exclude_unset=True)

    for field, value in modify_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    db.refresh(task)

    return task


@router.delete("/{task_id}")
def delete_task(
    task: Task = Depends(require_task_project_member),
    db: Session = Depends(get_db),
):
    """Delete a task.

    Only project members can delete a task.

    Raises:
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    try:
        db.delete(task)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Success"}


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task: Task = Depends(require_task_project_member_with_relationships)):
    """Retrieve a task by ID.

    Only project members can retrieve a task.

    Returns:
        The requested task
    """
    return task


@router.get(
    "", response_model=list[TaskResponse], dependencies=[Depends(get_current_user)]
)
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
    assignee_data: TaskAssigneeCreate,
    task: Task = Depends(require_task_project_member),
    db: Session = Depends(get_db),
):
    """Add an assignee to a task.

    Only project members can add assignee to a task within a project.

    Args:
        assignee_data: username of the assignee(user).

    Raises:
        HTTPException: If the assignee is not found.
        HTTPException: If the assignee is not a member of the project.
        HTTPException: If the assignee is already assigned to the task.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    user_query = select(User).where(User.username == assignee_data.username)
    user = db.execute(user_query).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    project_member = get_project_membership(user.id, task.project_id, db)

    if project_member is None:
        raise HTTPException(
            status_code=403, detail="The user is not a member of the project."
        )

    task_assignee = get_task_assignee(task.id, user.id, db)

    if task_assignee:
        raise HTTPException(
            status_code=409, detail="The user is already assigned to the task."
        )

    task_assignee = TaskAssignee(task_id=task.id, user_id=user.id)

    try:
        db.add(task_assignee)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400)

    return {"message": "Success"}


@router.delete("/{task_id}/assignees/{user_id}")
def delete_task_assignee(
    user_id: UUID,
    task: Task = Depends(require_task_project_member),
    db: Session = Depends(get_db),
):
    """Delete an assignee from a task.

    Only project members can remove assignee from a task.

    Args:
        user_id: ID of the user.

    Raises:
        HTTPException: If the user is not assigned to the task.
        HTTPException: If database integrity constraint is violated.

    Returns:
        Confirmation message.
    """
    task_assignee = get_task_assignee(task.id, user_id, db)

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
