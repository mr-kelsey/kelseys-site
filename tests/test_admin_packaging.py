import logging
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from app.db import Database
from app.models import Packaging

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

VALID_PACKAGING_FORM = {
    "name": "Lip Balm Tubes",
    "supplier": "China",
    "purchase_volume": "1000",
    "purchase_price": "810",
    "moq_for_price": "1000",
}


def _insert_packaging(db: Database) -> int:
    inserted = db.packaging.insert(
        Packaging(
            name="Lip Balm Tubes",
            supplier="China",
            purchase_volume=1000,
            purchase_price=810,
            moq_for_price=1000,
            created_at="2024-01-01T00:00:00+00:00",
        )
    )
    return inserted.id


def test_get_admin_packaging_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/packaging", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_packaging_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/packaging")
    assert response.status_code == 200


def test_get_admin_packaging_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/packaging/new")
    assert response.status_code == 200


def test_post_admin_packaging_new_creates_packaging(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/packaging/new", data=VALID_PACKAGING_FORM)
    assert db.packaging.count == 1


def test_post_admin_packaging_new_redirects_to_admin_packaging(
    admin_client: TestClient,
) -> None:
    response = admin_client.post(
        "/admin/packaging/new", data=VALID_PACKAGING_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/packaging"


def test_post_admin_packaging_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/packaging/new", data=VALID_PACKAGING_FORM)
    assert db.packaging.count == 0


def test_get_admin_packaging_edit_returns_200_for_existing_id(
    admin_client: TestClient, db: Database
) -> None:
    packaging_id = _insert_packaging(db)
    response = admin_client.get(f"/admin/packaging/{packaging_id}/edit")
    assert response.status_code == 200


def test_get_admin_packaging_edit_shows_existing_name(
    admin_client: TestClient, db: Database
) -> None:
    packaging_id = _insert_packaging(db)
    response = admin_client.get(f"/admin/packaging/{packaging_id}/edit")
    assert "Lip Balm Tubes" in response.text


def test_get_admin_packaging_edit_returns_404_for_unknown_id(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/packaging/999/edit")
    assert response.status_code == 404


def test_post_admin_packaging_edit_updates_name(
    admin_client: TestClient, db: Database
) -> None:
    packaging_id = _insert_packaging(db)
    updated_form = {**VALID_PACKAGING_FORM, "name": "Jar Lids"}
    admin_client.post(f"/admin/packaging/{packaging_id}/edit", data=updated_form)
    assert db.packaging.get(packaging_id).name == "Jar Lids"


def test_post_admin_packaging_edit_redirects_to_admin_packaging(
    admin_client: TestClient, db: Database
) -> None:
    packaging_id = _insert_packaging(db)
    response = admin_client.post(
        f"/admin/packaging/{packaging_id}/edit",
        data=VALID_PACKAGING_FORM,
        follow_redirects=False,
    )
    assert response.headers["location"] == "/admin/packaging"


def test_post_admin_packaging_delete_removes_packaging(
    admin_client: TestClient, db: Database
) -> None:
    packaging_id = _insert_packaging(db)
    admin_client.post(f"/admin/packaging/{packaging_id}/delete")
    assert db.packaging.count == 0


def test_post_admin_packaging_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    packaging_id = _insert_packaging(db)
    client.post(f"/admin/packaging/{packaging_id}/delete")
    assert db.packaging.count == 1


def test_creating_packaging_is_logged(
    admin_client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.INFO)
    admin_client.post("/admin/packaging/new", data=VALID_PACKAGING_FORM)
    assert "lip balm tubes" in caplog.text.lower()


def test_deleting_packaging_is_logged(
    admin_client: TestClient, db: Database, caplog: "LogCaptureFixture"
) -> None:
    packaging_id = _insert_packaging(db)
    caplog.set_level(logging.WARNING)
    admin_client.post(f"/admin/packaging/{packaging_id}/delete")
    assert "lip balm tubes" in caplog.text.lower()
