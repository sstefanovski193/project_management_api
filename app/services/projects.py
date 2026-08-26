from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProjectMember, ProjectRole


def get_project_membership(
    user_id: UUID, project_id: UUID, db: Session
) -> ProjectMember | None:
    """Retrieve user membership in a project.

    Args:
        user_id: ID of the user.
        project_id: ID of the project.
        db: SQLAlchemy database Session.

    Returns:
        Project membership if found or None.
    """
    project_membership_query = select(ProjectMember).where(
        ProjectMember.user_id == user_id, ProjectMember.project_id == project_id
    )

    return db.execute(project_membership_query).scalar_one_or_none()


def is_project_manager(user_id: UUID, project_id: UUID, db: Session) -> bool:
    """Retrieve user manager membership in a project.

    Args:
        project_id: ID of the project.
        user_id: ID of the user.
        db: SQLAlchemy database Session.

    Returns:
       Manager membership if found, otherwise None.
    """
    # TODO: improve authorization
    manager_query = select(ProjectMember).where(
        ProjectMember.user_id == user_id,
        ProjectMember.project_id == project_id,
        ProjectMember.role == ProjectRole.MANAGER,
    )

    return db.execute(manager_query).scalar_one_or_none() is not None
