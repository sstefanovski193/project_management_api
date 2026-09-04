from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def test_login_success(client, user):
    response = client.post(
        "/auth/login",
        data={"username": user.username, "password": "test_user_password"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data.get("access_token")
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, user):
    response = client.post(
        "/auth/login",
        data={"username": user.username, "password": "incorrect_test_user_password"},
    )

    assert response.status_code == 401


def test_login_unknown_username(client):
    response = client.post(
        "/auth/login",
        data={"username": "incorrect_username", "password": "test_user_password"},
    )

    assert response.status_code == 401


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/users",
        headers={"Authorization": "Bearer invalid_token"},
    )

    assert response.status_code == 401


def test_get_current_user_with_missing_user(client, db, user):
    login_response = client.post(
        "/auth/login",
        data={"username": user.username, "password": "test_user_password"},
    )

    assert login_response.status_code == 200

    token = login_response.json().get("access_token")

    db.delete(user)
    db.commit()

    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_get_current_user_with_token_without_subject(client, user):
    login_response = client.post(
        "/auth/login",
        data={"username": user.username, "password": "test_user_password"},
    )

    assert login_response.status_code == 200

    token = login_response.json().get("access_token")
    decoded_token = jwt.decode(
        jwt=token, key=settings.jwt_secret_key, algorithms=settings.jwt_algorithm
    )
    del decoded_token["sub"]

    encoded_token = jwt.encode(
        payload=decoded_token,
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/users", headers={"Authorization": f"Bearer {encoded_token}"}
    )

    assert response.status_code == 401


def test_get_current_user_with_expired_token(client, user):
    login_response = client.post(
        "/auth/login",
        data={"username": user.username, "password": "test_user_password"},
    )

    assert login_response.status_code == 200

    token = login_response.json().get("access_token")
    decoded_token = jwt.decode(
        jwt=token, key=settings.jwt_secret_key, algorithms=settings.jwt_algorithm
    )
    decoded_token["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)

    encoded_token = jwt.encode(
        payload=decoded_token,
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/users", headers={"Authorization": f"Bearer {encoded_token}"}
    )

    assert response.status_code == 401
