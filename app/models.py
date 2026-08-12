from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UUID as SQLAlchemyUUID,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ApplicationRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class Status(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ProjectRole(str, Enum):
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    application_role: Mapped[ApplicationRole] = mapped_column(
        SQLAlchemyEnum(ApplicationRole), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_tasks: Mapped[list["Task"]] = relationship(back_populates="creator")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        back_populates="user"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        secondary="task_assignees", back_populates="asignees"
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"

    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    project_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
        index=True,
    )
    role: Mapped[ProjectRole] = mapped_column(
        SQLAlchemyEnum(ProjectRole), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    user: Mapped["User"] = relationship(back_populates="project_memberships")
    project: Mapped["Project"] = relationship(back_populates="memberships")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    creator_id: Mapped[UUID | None] = mapped_column(
        SQLAlchemyUUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[Status] = mapped_column(SQLAlchemyEnum(Status), nullable=False)
    priority: Mapped[Priority] = mapped_column(SQLAlchemyEnum(Priority), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    project: Mapped["Project"] = relationship(back_populates="tasks")
    creator: Mapped["User | None"] = relationship(back_populates="created_tasks")
    asignees: Mapped[list["User"]] = relationship(
        secondary="task_asignees", back_populates="assigned_tasks"
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="task")


class TaskAsignee(Base):
    __tablename__ = "task_asignees"

    task_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID, primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        SQLAlchemyUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    task: Mapped["Task"] = relationship(back_populates="comments")
    author: Mapped["User | None"] = relationship(back_populates="comments")
