from starlette.testclient import TestClient

from app.db import Database
from app.models import Post


def test_returns_200_for_blog_index(client: TestClient) -> None:
    response = client.get("/blog")
    assert response.status_code == 200


def test_blog_index_lists_seeded_post_title(client: TestClient, db: Database) -> None:
    db.posts.insert(Post(slug="first-post", title="First Post", body="body"))
    response = client.get("/blog")
    assert "First Post" in response.text


def test_returns_200_for_known_post_slug(client: TestClient, db: Database) -> None:
    db.posts.insert(Post(slug="first-post", title="First Post", body="body"))
    response = client.get("/blog/first-post")
    assert response.status_code == 200


def test_post_detail_shows_body(client: TestClient, db: Database) -> None:
    db.posts.insert(Post(slug="first-post", title="First Post", body="The full post body."))
    response = client.get("/blog/first-post")
    assert "The full post body." in response.text


def test_returns_404_for_unknown_post_slug(client: TestClient) -> None:
    response = client.get("/blog/does-not-exist")
    assert response.status_code == 404


def test_post_detail_splits_body_into_separate_paragraph_tags(client: TestClient, db: Database) -> None:
    db.posts.insert(
        Post(slug="first-post", title="First Post", body="First paragraph.\n\nSecond paragraph.")
    )
    response = client.get("/blog/first-post")
    assert "First paragraph.</p>" in response.text
