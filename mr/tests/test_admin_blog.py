import logging
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from app.db import Database
from app.models import Post

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

VALID_POST_FORM = {
    "slug": "new-post",
    "title": "New Post",
    "body": "Paragraph one.\n\nParagraph two.",
}


def _insert_post(db: Database) -> None:
    db.posts.insert(
        Post(
            slug="new-post",
            title="New Post",
            body="Paragraph one.",
            created_at="2024-01-01T00:00:00+00:00",
        )
    )


def test_get_admin_blog_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/blog", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_blog_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/blog")
    assert response.status_code == 200


def test_get_admin_blog_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/blog/new")
    assert response.status_code == 200


def test_admin_blog_list_shows_logout_control(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/blog")
    assert 'action="/admin/logout"' in response.text


def test_admin_blog_list_new_post_link_is_in_its_own_block(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/blog")
    assert 'class="admin-action"' in response.text


def test_post_admin_blog_new_creates_post(admin_client: TestClient, db: Database) -> None:
    admin_client.post("/admin/blog/new", data=VALID_POST_FORM)
    assert db.posts.count == 1


def test_post_admin_blog_new_redirects_to_admin_blog(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/admin/blog/new", data=VALID_POST_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/blog"


def test_post_admin_blog_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/blog/new", data=VALID_POST_FORM)
    assert db.posts.count == 0


def test_get_admin_blog_edit_returns_200_for_existing_slug(
    admin_client: TestClient, db: Database
) -> None:
    _insert_post(db)
    response = admin_client.get("/admin/blog/new-post/edit")
    assert response.status_code == 200


def test_get_admin_blog_edit_shows_existing_title(
    admin_client: TestClient, db: Database
) -> None:
    _insert_post(db)
    response = admin_client.get("/admin/blog/new-post/edit")
    assert "New Post" in response.text


def test_get_admin_blog_edit_returns_404_for_unknown_slug(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/blog/does-not-exist/edit")
    assert response.status_code == 404


def test_post_admin_blog_edit_updates_title(
    admin_client: TestClient, db: Database
) -> None:
    _insert_post(db)
    updated_form = {**VALID_POST_FORM, "title": "Updated Title"}
    admin_client.post("/admin/blog/new-post/edit", data=updated_form)
    [post] = db.posts(where="slug=?", where_args=["new-post"])
    assert post.title == "Updated Title"


def test_post_admin_blog_edit_redirects_to_admin_blog(
    admin_client: TestClient, db: Database
) -> None:
    _insert_post(db)
    response = admin_client.post(
        "/admin/blog/new-post/edit", data=VALID_POST_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/blog"


def test_post_admin_blog_delete_removes_post(
    admin_client: TestClient, db: Database
) -> None:
    _insert_post(db)
    admin_client.post("/admin/blog/new-post/delete")
    assert db.posts.count == 0


def test_post_admin_blog_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    _insert_post(db)
    client.post("/admin/blog/new-post/delete")
    assert db.posts.count == 1


def test_creating_post_is_logged(
    admin_client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.INFO)
    admin_client.post("/admin/blog/new", data=VALID_POST_FORM)
    assert "new-post" in caplog.text


def test_deleting_post_is_logged(
    admin_client: TestClient, db: Database, caplog: "LogCaptureFixture"
) -> None:
    _insert_post(db)
    caplog.set_level(logging.WARNING)
    admin_client.post("/admin/blog/new-post/delete")
    assert "new-post" in caplog.text
