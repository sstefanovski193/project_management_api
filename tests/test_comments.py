from uuid import uuid4

from app.models import Comment
from app.services.comments import get_comment_by_id


def test_create_comment(client, task, auth_headers):
    payload = {"content": "Comment Test Data"}
    response = client.post(
        f"/tasks/{task.id}/comments", headers=auth_headers, json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["content"] == "Comment Test Data"


def test_create_comment_requires_authentication(client, task):
    payload = {"content": "Comment Test Data"}
    response = client.post(f"/tasks/{task.id}/comments", json=payload)

    assert response.status_code == 401


def test_create_comment_requires_task_project_member(
    client, task, another_auth_headers
):
    payload = {"content": "Comment Test Data"}
    response = client.post(
        f"/tasks/{task.id}/comments", headers=another_auth_headers, json=payload
    )

    assert response.status_code == 403


def test_create_comment_task_not_found(client, auth_headers):
    payload = {"content": "Comment Test Data"}
    response = client.post(
        f"/tasks/{str(uuid4())}/comments", headers=auth_headers, json=payload
    )

    assert response.status_code == 404


def test_modify_comment(client, comment, auth_headers):
    payload = {"content": "Updated Comment Test Data"}
    response = client.patch(
        f"/comments/{comment.id}", headers=auth_headers, json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["content"] == "Updated Comment Test Data"


def test_modify_comment_requires_authentication(client, comment):
    payload = {"content": "Updated Comment Test Data"}
    response = client.patch(f"/comments/{comment.id}", json=payload)

    assert response.status_code == 401


def test_modify_comment_requires_comment_author(
    client, comment, project_member, another_auth_headers
):
    payload = {"content": "Updated Comment Test Data"}
    response = client.patch(
        f"/comments/{comment.id}", headers=another_auth_headers, json=payload
    )

    assert response.status_code == 403


def test_modify_comment_comment_not_found(client, auth_headers):
    payload = {"content": "Updated Comment Test Data"}
    response = client.patch(
        f"/comments/{str(uuid4())}", headers=auth_headers, json=payload
    )

    assert response.status_code == 404


def test_delete_comment_by_author(client, comment, auth_headers, user, db):
    assert comment.user_id == user.id

    response = client.delete(f"/comments/{comment.id}", headers=auth_headers)

    assert response.status_code == 200

    comment = get_comment_by_id(comment.id, db)

    assert comment is None


def test_delete_comment_by_project_manager(
    client, task, project_member, auth_headers, another_user, user, db
):
    comment = Comment(
        task_id=task.id, user_id=another_user.id, content="Comment Test Data"
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    assert comment.user_id != user.id

    response = client.delete(f"/comments/{comment.id}", headers=auth_headers)

    assert response.status_code == 200

    comment = get_comment_by_id(comment.id, db)

    assert comment is None


def test_delete_comment_requires_authentication(client, comment):
    response = client.delete(f"/comments/{comment.id}")

    assert response.status_code == 401


def test_delete_comment_requires_author_or_project_manager(
    client, comment, project_member, another_auth_headers
):
    response = client.delete(f"/comments/{comment.id}", headers=another_auth_headers)

    assert response.status_code == 403


def test_delete_comment_comment_not_found(client, auth_headers):
    response = client.delete(f"/comments/{str(uuid4())}", headers=auth_headers)

    assert response.status_code == 404


def test_get_comment(client, comment, auth_headers):
    response = client.get(f"/comments/{comment.id}", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data["content"] == comment.content


def test_get_comment_requires_authentication(client, comment):
    response = client.get(f"/comments/{comment.id}")

    assert response.status_code == 401


def test_get_comment_requires_project_member(client, comment, another_auth_headers):
    response = client.get(f"/comments/{comment.id}", headers=another_auth_headers)

    assert response.status_code == 403


def test_get_comment_comment_not_found(client, auth_headers):
    response = client.get(f"/comments/{str(uuid4())}", headers=auth_headers)

    assert response.status_code == 404
