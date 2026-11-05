from collections.abc import Iterator
from os import close as close_fd
from pathlib import Path
from tempfile import mkstemp

from fastlite import NotFoundError
from pytest import fixture, raises

from app.db import Database
from app.models import ContactMessage, Post, Project


@fixture()
def db() -> Iterator[Database]:
    file_descriptor, db_path = mkstemp(suffix=".db")
    close_fd(file_descriptor)
    db_path = Path(db_path)
    try:
        yield Database(str(db_path))
    finally:
        db_path.unlink()


def test_creates_projects_table(db: Database) -> None:
    assert "projects" in db.connection.table_names()


def test_creates_posts_table(db: Database) -> None:
    assert "posts" in db.connection.table_names()


def test_creates_contact_messages_table(db: Database) -> None:
    assert "contact_messages" in db.connection.table_names()


def test_inserted_project_is_retrievable_by_slug(db: Database) -> None:
    db.projects.insert(Project(slug="hospital-cv", title="Hospital CV", description="d", url=""))
    found = db.projects(where="slug=?", where_args=["hospital-cv"])
    assert found[0].title == "Hospital CV"


def test_missing_project_slug_returns_no_rows(db: Database) -> None:
    found = db.projects(where="slug=?", where_args=["does-not-exist"])
    assert found == []


def test_inserted_post_is_retrievable_by_slug(db: Database) -> None:
    db.posts.insert(Post(slug="first-post", title="First Post", body="body"))
    found = db.posts(where="slug=?", where_args=["first-post"])
    assert found[0].title == "First Post"


def test_inserted_contact_message_is_persisted(db: Database) -> None:
    db.contact_messages.insert(
        ContactMessage(name="Alex", email="alex@example.com", message="Hi")
    )
    assert db.contact_messages.count == 1


def test_project_get_raises_for_unknown_id(db: Database) -> None:
    with raises(NotFoundError):
        db.projects.get(999)


def test_inserted_project_body_is_retrievable_by_slug(db: Database) -> None:
    db.projects.insert(
        Project(slug="hospital-cv", title="Hospital CV", description="d", body="Full case study.", url="")
    )
    found = db.projects(where="slug=?", where_args=["hospital-cv"])
    assert found[0].body == "Full case study."
