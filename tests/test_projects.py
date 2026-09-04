from uuid import UUID, uuid4

from app.services.projects import get_project_membership, get_project_by_id
from app.models import ProjectRole, Project
from app.schemas.projects import ProjectSortField
from app.schemas.common import SortOrder


def test_create_project(client, auth_headers, user, db):
    response = client.post(
        "/projects",
        headers=auth_headers,
        json={"name": "Project Name", "description": "Project Description"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data.get("name") == "Project Name"
    assert data.get("description") == "Project Description"

    project_membership = get_project_membership(user.id, data.get("id"), db)

    assert project_membership.role == ProjectRole.MANAGER


def test_create_project_requies_authenticated_user(client):
    response = client.post(
        "/projects", json={"name": "Project Name", "description": "Project Description"}
    )

    assert response.status_code == 401


def test_get_project(client, auth_headers, project):
    response = client.get(f"/projects/{project.id}", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert UUID(data["id"]) == project.id
    assert data["name"] == project.name
    assert data["description"] == project.description


def test_get_project_not_found(client, auth_headers):
    response = client.get(f"/projects/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404


def test_get_project_requires_authentication(client, project):
    response = client.get(f"/projects/{project.id}")

    assert response.status_code == 401


def test_get_project_requires_project_member(client, project, another_auth_headers):
    response = client.get(f"/projects/{project.id}", headers=another_auth_headers)

    assert response.status_code == 403


def test_get_projects(client, auth_headers, project):
    response = client.get("/projects", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()

    assert data[0]["name"] == project.name
    assert data[0]["description"] == project.description


def test_get_projects_requires_authentication(client):
    response = client.get("/projects")

    assert response.status_code == 401


def test_get_projects_pagination(client, auth_headers, db):
    project_a = Project(name="Project A", description="Project A Description")
    project_b = Project(name="Project B", description="Project B Description")
    project_c = Project(name="Project C", description="Project C Description")

    db.add_all([project_a, project_b, project_c])
    db.commit()

    payload = {
        "limit": 2,
        "offset": 1,
        "sort_by": ProjectSortField.NAME.value,
        "sort_order": SortOrder.ASC.value,
    }

    response = client.get("/projects", headers=auth_headers, params=payload)

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == project_b.name
    assert data[1]["name"] == project_c.name


def test_get_projects_sort_by_name(client, auth_headers, db):
    project_a = Project(name="Project A", description="Project A Description")
    project_b = Project(name="Project B", description="Project B Description")
    project_c = Project(name="Project C", description="Project C Description")

    db.add_all([project_a, project_b, project_c])
    db.commit()

    payload = {
        "sort_by": ProjectSortField.NAME.value,
        "sort_order": SortOrder.ASC.value,
    }

    response = client.get("/projects", headers=auth_headers, params=payload)

    assert response.status_code == 200

    data = response.json()

    assert data[0]["name"] == project_a.name
    assert data[1]["name"] == project_b.name
    assert data[2]["name"] == project_c.name


def test_add_project_member(client, auth_headers, project, another_user):
    payload = {"user_id": str(another_user.id)}
    response = client.post(
        f"/projects/{project.id}/members",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["role"] == ProjectRole.MEMBER.value
    assert data["user"]["id"] == str(another_user.id)


def test_add_project_member_requires_authentication(client, project, another_user):
    payload = {"user_id": str(another_user.id)}
    response = client.post(f"/projects/{project.id}/members", json=payload)

    assert response.status_code == 401


def test_add_project_member_requires_project_manager(
    client, project, another_auth_headers, another_user
):
    payload = {"user_id": str(another_user.id)}
    response = client.post(
        f"/projects/{project.id}/members", headers=another_auth_headers, json=payload
    )

    assert response.status_code == 403


def test_add_project_member_user_not_found(client, project, auth_headers):
    payload = {"user_id": str(uuid4())}
    response = client.post(
        f"/projects/{project.id}/members", headers=auth_headers, json=payload
    )

    assert response.status_code == 404


def test_add_project_member_user_already_member(client, project, auth_headers, user):
    payload = {"user_id": str(user.id)}
    response = client.post(
        f"/projects/{project.id}/members", headers=auth_headers, json=payload
    )

    assert response.status_code == 409


def test_delete_project_member(
    client, project, project_member, auth_headers, another_user, db
):
    response = client.delete(
        f"/projects/{project.id}/members/{another_user.id}", headers=auth_headers
    )

    assert response.status_code == 200

    project_membership = get_project_membership(another_user.id, project.id, db)

    assert project_membership is None


def test_delete_project_member_requires_authentication(
    client, project, project_member, another_user
):
    response = client.delete(f"/projects/{project.id}/members/{another_user.id}")

    assert response.status_code == 401


def test_delete_project_member_requires_project_manager(
    client, project, project_member, another_auth_headers, another_user
):
    response = client.delete(
        f"/projects/{project.id}/members/{another_user.id}",
        headers=another_auth_headers,
    )

    assert response.status_code == 403


def test_delete_project_membership_not_found(
    client, project, auth_headers, another_user
):
    response = client.delete(
        f"/projects/{project.id}/members/{another_user.id}", headers=auth_headers
    )

    assert response.status_code == 404


def test_delete_project(client, project, admin_auth_headers, db):
    response = client.delete(f"/projects/{project.id}", headers=admin_auth_headers)

    assert response.status_code == 200

    project = get_project_by_id(project.id, db)

    assert project is None


def test_delete_project_not_found(client, admin_auth_headers):
    response = client.delete(f"/projects/{uuid4()}", headers=admin_auth_headers)

    assert response.status_code == 404


def test_delete_project_requires_authentication(client, project):
    response = client.delete(f"/projects/{project.id}")

    assert response.status_code == 401


def test_delete_project_requires_admin_user(client, project, auth_headers):
    response = client.delete(f"/projects/{project.id}", headers=auth_headers)

    assert response.status_code == 403


def test_delete_project_containing_tasks(client, project, task, admin_auth_headers):
    response = client.delete(f"/projects/{project.id}", headers=admin_auth_headers)

    assert response.status_code == 409
