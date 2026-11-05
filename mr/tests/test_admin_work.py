import logging
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from app.db import Database
from app.models import Project

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

VALID_PROJECT_FORM = {
    "slug": "new-project",
    "title": "New Project",
    "description": "A short teaser.",
    "body": "Paragraph one.\n\nParagraph two.",
    "url": "https://github.com/mr-kelsey/new-project",
    "report_pdf": "",
}


def _insert_project(db: Database) -> None:
    db.projects.insert(
        Project(
            slug="new-project",
            title="New Project",
            description="A short teaser.",
            body="Paragraph one.",
            url="https://github.com/mr-kelsey/new-project",
            report_pdf="",
            created_at="2024-01-01T00:00:00+00:00",
        )
    )


def test_get_admin_work_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/work", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_work_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/work")
    assert response.status_code == 200


def test_get_admin_work_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/work/new")
    assert response.status_code == 200


def test_admin_work_list_shows_logout_control(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/work")
    assert 'action="/admin/logout"' in response.text


def test_admin_work_list_new_project_link_is_in_its_own_block(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/work")
    assert 'class="admin-action"' in response.text


def test_post_admin_work_new_creates_project(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/work/new", data=VALID_PROJECT_FORM)
    assert db.projects.count == 1


def test_post_admin_work_new_redirects_to_admin_work(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/admin/work/new", data=VALID_PROJECT_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/work"


def test_post_admin_work_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/work/new", data=VALID_PROJECT_FORM)
    assert db.projects.count == 0


def test_get_admin_work_edit_returns_200_for_existing_slug(
    admin_client: TestClient, db: Database
) -> None:
    _insert_project(db)
    response = admin_client.get("/admin/work/new-project/edit")
    assert response.status_code == 200


def test_get_admin_work_edit_shows_existing_title(
    admin_client: TestClient, db: Database
) -> None:
    _insert_project(db)
    response = admin_client.get("/admin/work/new-project/edit")
    assert "New Project" in response.text


def test_get_admin_work_edit_returns_404_for_unknown_slug(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/work/does-not-exist/edit")
    assert response.status_code == 404


def test_post_admin_work_edit_updates_title(
    admin_client: TestClient, db: Database
) -> None:
    _insert_project(db)
    updated_form = {**VALID_PROJECT_FORM, "title": "Updated Title"}
    admin_client.post("/admin/work/new-project/edit", data=updated_form)
    [project] = db.projects(where="slug=?", where_args=["new-project"])
    assert project.title == "Updated Title"


def test_post_admin_work_edit_redirects_to_admin_work(
    admin_client: TestClient, db: Database
) -> None:
    _insert_project(db)
    response = admin_client.post(
        "/admin/work/new-project/edit", data=VALID_PROJECT_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/work"


def test_post_admin_work_delete_removes_project(
    admin_client: TestClient, db: Database
) -> None:
    _insert_project(db)
    admin_client.post("/admin/work/new-project/delete")
    assert db.projects.count == 0


def test_post_admin_work_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    _insert_project(db)
    client.post("/admin/work/new-project/delete")
    assert db.projects.count == 1


def test_creating_project_is_logged(
    admin_client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.INFO)
    admin_client.post("/admin/work/new", data=VALID_PROJECT_FORM)
    assert "new-project" in caplog.text


def test_deleting_project_is_logged(
    admin_client: TestClient, db: Database, caplog: "LogCaptureFixture"
) -> None:
    _insert_project(db)
    caplog.set_level(logging.WARNING)
    admin_client.post("/admin/work/new-project/delete")
    assert "new-project" in caplog.text
