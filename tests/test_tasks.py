from uuid import uuid4

from app.models import Status, Priority, Task
from app.schemas.tasks import TaskSortField
from app.schemas.common import SortOrder
from app.services.tasks import get_task_assignee, get_task_by_id


def test_create_task(client, project, auth_headers, user):
    payload = {
        "project_id": str(project.id),
        "creator_id": str(user.id),
        "title": "Test Task",
    }
    response = client.post(
        f"/projects/{project.id}/tasks", headers=auth_headers, json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == str(project.id)
    assert data["title"] == "Test Task"
    assert data["description"] is None
    assert data["status"] == Status.TODO.value
    assert data["priority"] == Priority.MEDIUM.value


def test_create_task_requires_authentication(client, project, user):
    payload = {
        "project_id": str(project.id),
        "creator_id": str(user.id),
        "title": "Test Task",
    }
    response = client.post(f"/projects/{project.id}/tasks", json=payload)

    assert response.status_code == 401


def test_create_task_requires_project_member(
    client, project, another_auth_headers, another_user
):
    payload = {
        "project_id": str(project.id),
        "creator_id": str(another_user.id),
        "title": "Test Task",
    }
    response = client.post(
        f"/projects/{project.id}/tasks", headers=another_auth_headers, json=payload
    )

    assert response.status_code == 403


def test_create_task_project_not_found(client, auth_headers, user):
    project_id = uuid4()
    payload = {
        "project_id": str(project_id),
        "creator_id": str(user.id),
        "title": "Test Task",
    }
    response = client.post(
        f"/projects/{project_id}/tasks", headers=auth_headers, json=payload
    )

    assert response.status_code == 404


def test_modify_task(client, task, auth_headers):
    payload = {"description": "Test Task Description", "status": Status.DONE.value}
    response = client.patch(f"/tasks/{task.id}", headers=auth_headers, json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["description"] == "Test Task Description"
    assert data["status"] == Status.DONE.value
    assert data["title"] == "Test Task"


def test_modify_task_requires_authentication(client, task):
    payload = {"description": "Test Task Description", "status": Status.DONE.value}
    response = client.patch(f"/tasks/{task.id}", json=payload)

    assert response.status_code == 401


def test_modify_task_requires_project_member(client, task, another_auth_headers):
    payload = {"description": "Test Task Description", "status": Status.DONE.value}
    response = client.patch(
        f"/tasks/{task.id}", headers=another_auth_headers, json=payload
    )

    assert response.status_code == 403


def test_modify_task_task_not_found(client, auth_headers):
    payload = {"description": "Test Task Description", "status": Status.DONE.value}
    response = client.patch(
        f"/tasks/{str(uuid4())}", headers=auth_headers, json=payload
    )

    assert response.status_code == 404


def test_delete_task(client, task, auth_headers, db):
    response = client.delete(f"/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 200

    task = get_task_by_id(task.id, db)

    assert task is None


def test_delete_task_requires_authentication(client, task):
    response = client.delete(f"/tasks/{task.id}")

    assert response.status_code == 401


def test_delete_task_requires_project_member(client, task, another_auth_headers):
    response = client.delete(f"/tasks/{task.id}", headers=another_auth_headers)

    assert response.status_code == 403


def test_delete_task_task_not_found(client, auth_headers):
    response = client.delete(f"/tasks/{str(uuid4())}", headers=auth_headers)

    assert response.status_code == 404


def test_get_task(client, task, auth_headers):
    response = client.get(f"/tasks/{task.id}", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Test Task"
    assert data["status"] == Status.TODO.value
    assert data["priority"] == Priority.MEDIUM.value


def test_get_task_requires_authentication(client, task):
    response = client.get(f"/tasks/{task.id}")

    assert response.status_code == 401


def test_get_task_requires_project_member(client, task, another_auth_headers):
    response = client.get(f"/tasks/{task.id}", headers=another_auth_headers)

    assert response.status_code == 403


def test_get_task_task_not_found(client, auth_headers):
    response = client.get(f"/tasks/{str(uuid4())}", headers=auth_headers)

    assert response.status_code == 404


def test_get_tasks(client, task, auth_headers):
    response = client.get("/tasks", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data[0]["id"] == str(task.id)
    assert data[0]["title"] == task.title


def test_get_tasks_requires_authentication(client):
    response = client.get("/tasks")

    assert response.status_code == 401


def test_get_tasks_sort_by_updated_at(client, project, auth_headers, db):
    task_a = Task(
        project_id=project.id,
        title="Task A",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )
    task_b = Task(
        project_id=project.id,
        title="Task B",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )
    task_c = Task(
        project_id=project.id,
        title="Task C",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )

    db.add_all([task_a, task_b, task_c])
    db.commit()
    db.refresh(task_a)
    db.refresh(task_b)
    db.refresh(task_c)

    payload = {
        "sort_by": TaskSortField.TITLE.value,
        "sort_order": SortOrder.DESC.value,
    }

    response = client.get("/tasks", headers=auth_headers, params=payload)

    assert response.status_code == 200

    data = response.json()

    assert data[0]["title"] == task_c.title
    assert data[1]["title"] == task_b.title
    assert data[2]["title"] == task_a.title


def test_get_tasks_pagination(client, project, auth_headers, db):
    task_a = Task(
        project_id=project.id,
        title="Task A",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )
    task_b = Task(
        project_id=project.id,
        title="Task B",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )
    task_c = Task(
        project_id=project.id,
        title="Task C",
        status=Status.TODO,
        priority=Priority.MEDIUM,
    )

    db.add_all([task_a, task_b, task_c])
    db.commit()

    payload = {
        "limit": 2,
        "offset": 1,
        "sort_by": TaskSortField.TITLE.value,
        "sort_order": SortOrder.ASC.value,
    }

    response = client.get("/tasks", headers=auth_headers, params=payload)

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == task_b.title
    assert data[1]["title"] == task_c.title


def test_add_task_assignee(client, task, auth_headers, project_member, another_user):
    payload = {"username": another_user.username}
    response = client.post(
        f"/tasks/{task.id}/assignees", headers=auth_headers, json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {"message": "Success"}


def test_add_task_assignee_requires_authentication(
    client, task, project_member, another_user
):
    payload = {"username": another_user.username}
    response = client.post(f"/tasks/{task.id}/assignees", json=payload)

    assert response.status_code == 401


def test_add_task_assignee_requires_assignee_to_be_project_member(
    client, task, auth_headers, another_user
):
    payload = {"username": another_user.username}
    response = client.post(
        f"/tasks/{task.id}/assignees", headers=auth_headers, json=payload
    )

    assert response.status_code == 403


def test_add_task_assignee_task_not_found(client, auth_headers, another_user):
    payload = {"username": another_user.username}
    response = client.post(
        f"/tasks/{str(uuid4())}/assignees", headers=auth_headers, json=payload
    )

    assert response.status_code == 404


def test_add_task_assignee_already_assigned(
    client, task, auth_headers, user, task_assignee
):
    payload = {"username": user.username}
    response = client.post(
        f"/tasks/{task.id}/assignees", headers=auth_headers, json=payload
    )

    assert response.status_code == 409


def test_delete_task_assignee(client, task, task_assignee, auth_headers, user, db):
    response = client.delete(
        f"/tasks/{task.id}/assignees/{user.id}", headers=auth_headers
    )

    assert response.status_code == 200

    task_assignee = get_task_assignee(task.id, user.id, db)

    assert task_assignee is None


def test_delete_task_assignee_requires_authentication(
    client, task, task_assignee, user
):
    response = client.delete(f"/tasks/{task.id}/assignees/{user.id}")

    assert response.status_code == 401


def test_delete_task_assignee_requires_project_member(
    client, task, another_auth_headers, task_assignee, user
):
    response = client.delete(
        f"/tasks/{task.id}/assignees/{user.id}", headers=another_auth_headers
    )

    assert response.status_code == 403


def test_delete_task_assignee_assignee_not_found(client, task, auth_headers):
    response = client.delete(
        f"/tasks/{task.id}/assignees/{str(uuid4())}", headers=auth_headers
    )

    assert response.status_code == 404


def test_delete_task_assignee_task_not_found(client, auth_headers, user):
    response = client.delete(
        f"/tasks/{str(uuid4())}/assignees/{str(user.id)}", headers=auth_headers
    )

    assert response.status_code == 404
