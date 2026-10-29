from importlib import import_module
from os import close as close_fd
from pathlib import Path
from sys import modules
from tempfile import mkstemp
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pytest import MonkeyPatch, fixture
from starlette.testclient import TestClient

if TYPE_CHECKING:
    from app.db import Database
    from app.email import EmailSender

ADMIN_PASSWORD_FOR_TESTS = "test-admin-password"


def _drop_app_modules() -> None:
    for module_name in list(modules):
        if module_name == "app" or module_name.startswith("app."):
            del modules[module_name]


@fixture()
def client(monkeypatch: MonkeyPatch) -> Iterator[TestClient]:
    """A TestClient wired to a fresh temp-file SQLite DB per test.

    app.db opens its connection at import time, so the app package is
    dropped from sys.modules and re-imported after DB_PATH is set, giving
    each test its own isolated database rather than a shared singleton.
    """
    file_descriptor, db_path = mkstemp(suffix=".db") # leaves fd in open state
    close_fd(file_descriptor) # closes fd to make sure it's not orphaned
    db_path = Path(db_path)
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD_FOR_TESTS)

    _drop_app_modules()
    main_module = import_module("app.main")

    try:
        with TestClient(main_module.app) as test_client:
            yield test_client
    finally:
        _drop_app_modules()
        db_path.unlink()


@fixture()
def db(client: TestClient) -> "Database":
    """The site's Database singleton for the test's own temp SQLite file.

    Depends on `client` so app.main (and transitively app.db) has already
    been re-imported against this test's DB_PATH — importing app.db here
    directly (instead of at module load time) fetches that same fresh
    instance from sys.modules rather than one bound to a stale path.
    """
    return import_module("app.db").site_db


@fixture()
def email_sender(client: TestClient) -> "EmailSender":
    """The site's EmailSender singleton — see `db` above for why this is
    fetched fresh via import_module rather than a module-level import."""
    return import_module("app.email").site_email_sender


@fixture()
def admin_client(client: TestClient) -> TestClient:
    """A `client` that has already logged in as admin via the real login route."""
    client.post("/admin/login", data={"password": ADMIN_PASSWORD_FOR_TESTS})
    return client
