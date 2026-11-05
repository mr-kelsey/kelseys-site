import logging
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from app.db import Database
from app.models import Product

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

VALID_PRODUCT_FORM = {
    "slug": "new-product",
    "name": "New Product",
    "description": "A short teaser.",
}


def _insert_product(db: Database) -> None:
    db.products.insert(
        Product(
            slug="new-product",
            name="New Product",
            description="A short teaser.",
            created_at="2024-01-01T00:00:00+00:00",
        )
    )


def test_get_admin_products_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/products", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_products_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/products")
    assert response.status_code == 200


def test_get_admin_products_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/products/new")
    assert response.status_code == 200


def test_post_admin_products_new_creates_product(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/products/new", data=VALID_PRODUCT_FORM)
    assert db.products.count == 1


def test_post_admin_products_new_redirects_to_admin_products(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/admin/products/new", data=VALID_PRODUCT_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/products"


def test_post_admin_products_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/products/new", data=VALID_PRODUCT_FORM)
    assert db.products.count == 0


def test_get_admin_products_edit_returns_200_for_existing_slug(
    admin_client: TestClient, db: Database
) -> None:
    _insert_product(db)
    response = admin_client.get("/admin/products/new-product/edit")
    assert response.status_code == 200


def test_get_admin_products_edit_returns_404_for_unknown_slug(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/products/does-not-exist/edit")
    assert response.status_code == 404


def test_post_admin_products_edit_updates_name(
    admin_client: TestClient, db: Database
) -> None:
    _insert_product(db)
    updated_form = {**VALID_PRODUCT_FORM, "name": "Updated Name"}
    admin_client.post("/admin/products/new-product/edit", data=updated_form)
    [product] = db.products(where="slug=?", where_args=["new-product"])
    assert product.name == "Updated Name"


def test_post_admin_products_new_sets_category(admin_client: TestClient, db: Database) -> None:
    admin_client.post("/admin/products/new", data={**VALID_PRODUCT_FORM, "category": "Balms"})
    [product] = db.products(where="slug=?", where_args=["new-product"])
    assert product.category == "Balms"


def test_post_admin_products_edit_updates_category(
    admin_client: TestClient, db: Database
) -> None:
    _insert_product(db)
    updated_form = {**VALID_PRODUCT_FORM, "category": "Balms"}
    admin_client.post("/admin/products/new-product/edit", data=updated_form)
    [product] = db.products(where="slug=?", where_args=["new-product"])
    assert product.category == "Balms"


def test_post_admin_products_delete_removes_product(
    admin_client: TestClient, db: Database
) -> None:
    _insert_product(db)
    admin_client.post("/admin/products/new-product/delete")
    assert db.products.count == 0


def test_post_admin_products_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    _insert_product(db)
    client.post("/admin/products/new-product/delete")
    assert db.products.count == 1


def test_creating_product_is_logged(
    admin_client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.INFO)
    admin_client.post("/admin/products/new", data=VALID_PRODUCT_FORM)
    assert "new-product" in caplog.text
