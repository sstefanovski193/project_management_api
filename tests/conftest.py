import os

os.environ["APP_ENV"] = "test"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.config import settings
from app.models import (
    Base,
    User,
    ApplicationRole,
    Project,
    ProjectRole,
    ProjectMember,
    Task,
    Status,
    Priority,
)
from app.db.database import get_db
from app.main import app
from app.security import hash_password

engine = create_engine(settings.database_url)

TestingSession = sessionmaker(autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create the test database schema for the test session."""
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Provide an isolated database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSession(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db):
    """Provide a test client using the isolated database session."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    """Create a regular user for testing."""
    user = User(
        username="test_user",
        email="test_user@email.com",
        password_hash=hash_password("test_user_password"),
        application_role=ApplicationRole.USER,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def admin_user(db):
    """Create an administrator for testing."""
    user = User(
        username="admin_test_user",
        email="admin_test_user@email.com",
        password_hash=hash_password("admin_test_user_password"),
        application_role=ApplicationRole.ADMIN,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def auth_headers(client, user):
    """Return authentication headers for a regular user."""
    response = client.post(
        "/auth/login",
        data={"username": user.username, "password": "test_user_password"},
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Return authentication headers for an admin user."""
    response = client.post(
        "/auth/login",
        data={"username": admin_user.username, "password": "admin_test_user_password"},
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project(db, user):
    """Create a project with the regular user as its manager."""
    project = Project(name="Project Name", description="Project Description")

    db.add(project)
    db.flush()

    project_membership = ProjectMember(
        user_id=user.id, project_id=project.id, role=ProjectRole.MANAGER
    )

    db.add(project_membership)
    db.commit()
    db.refresh(project)

    return project


@pytest.fixture
def another_user(db):
    """Create another regular user for testing."""
    another_user = User(
        username="another_test_user",
        email="another_test_user@email.com",
        password_hash=hash_password("another_test_user_password"),
        application_role=ApplicationRole.USER,
    )

    db.add(another_user)
    db.commit()
    db.refresh(another_user)

    return another_user


@pytest.fixture
def another_auth_headers(client, another_user):
    """Return authentication headers for another regular user."""
    response = client.post(
        "/auth/login",
        data={
            "username": another_user.username,
            "password": "another_test_user_password",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project_member(project, another_user, db):
    """Add another regular user to the project as a member."""
    project_member = ProjectMember(
        user_id=another_user.id, project_id=project.id, role=ProjectRole.MEMBER
    )

    db.add(project_member)
    db.commit()
    db.refresh(project_member)

    return project_member


@pytest.fixture
def task(project, db):
    """Create a task in the test project."""
    task = Task(
        project_id=project.id,
        title="Test Task",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task
