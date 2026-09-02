import os

os.environ["APP_ENV"] = "test"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.config import settings
from app.models import Base, User, ApplicationRole
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
