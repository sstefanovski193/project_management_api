from uuid import uuid4


def test_create_user(client):
    payload = {
        "username": "test_user",
        "email": "test_user@email.com",
        "password": "test_user_password",
    }
    response = client.post("/users", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "test_user"
    assert data["email"] == "test_user@email.com"
    assert data["application_role"] == "USER"

    assert "password" not in data
    assert "password_hash" not in data


def test_create_user_duplicate_username(client):
    payload = {
        "username": "test_user",
        "email": "test_user@email.com",
        "password": "test_user_password",
    }
    response = client.post("/users", json=payload)

    assert response.status_code == 200

    payload.update(email="test_user2@email.com")
    duplicate_response = client.post("/users", json=payload)

    assert duplicate_response.status_code == 409


def test_create_user_duplicate_email(client):
    payload = {
        "username": "test_user",
        "email": "test_user@email.com",
        "password": "test_user_password",
    }
    response = client.post("/users", json=payload)

    assert response.status_code == 200

    payload.update(username="test_user2")
    duplicate_response = client.post("/users", json=payload)

    assert duplicate_response.status_code == 409


def test_create_user_cannot_register_as_admin(client):
    payload = {
        "username": "test_user",
        "email": "test_user@email.com",
        "password": "test_user_password",
        "application_role": "ADMIN",
    }
    response = client.post("/users", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["application_role"] == "USER"


def test_delete_user_requires_admin_authentication(client, auth_headers, user):
    response = client.delete(f"/users/{user.id}")

    assert response.status_code == 401

    authenticated_response = client.delete(f"/users/{user.id}", headers=auth_headers)

    assert authenticated_response.status_code == 403


def test_delete_user(client, admin_auth_headers, user):
    response = client.delete(f"/users/{user.id}", headers=admin_auth_headers)

    assert response.status_code == 200


def test_get_users_requires_authentication(client):
    response = client.get("/users")

    assert response.status_code == 401


def test_get_users(client, auth_headers, user):
    response = client.get("/users", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data[0]["id"] == str(user.id)
    assert data[0]["username"] == user.username
    assert data[0]["email"] == user.email


def test_get_user_requires_authentication(client, user):
    response = client.get(f"/users/{user.id}")

    assert response.status_code == 401


def test_get_user(client, auth_headers, user):
    response = client.get(f"/users/{user.id}", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["username"] == user.username
    assert data["email"] == user.email


def test_get_user_not_found(client, auth_headers):
    response = client.get(f"/users/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404
