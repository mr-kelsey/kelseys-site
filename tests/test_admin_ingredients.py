import logging
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from app.db import Database
from app.models import Ingredient

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

VALID_INGREDIENT_FORM = {
    "name": "White Beeswax",
    "vendor": "Mary Tyler Naturals",
    "purchase_volume": "16",
    "volume_unit": "oz",
    "total_grams": "453.59",
    "purchase_price": "12",
}


def _insert_ingredient(db: Database) -> int:
    inserted = db.ingredients.insert(
        Ingredient(
            name="White Beeswax",
            vendor="Mary Tyler Naturals",
            purchase_volume=16,
            volume_unit="oz",
            total_grams=453.59,
            purchase_price=12,
            created_at="2024-01-01T00:00:00+00:00",
        )
    )
    return inserted.id


def test_get_admin_ingredients_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/ingredients", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_ingredients_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/ingredients")
    assert response.status_code == 200


def test_get_admin_ingredients_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/ingredients/new")
    assert response.status_code == 200


def test_post_admin_ingredients_new_creates_ingredient(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/ingredients/new", data=VALID_INGREDIENT_FORM)
    assert db.ingredients.count == 1


def test_post_admin_ingredients_new_redirects_to_admin_ingredients(
    admin_client: TestClient,
) -> None:
    response = admin_client.post(
        "/admin/ingredients/new", data=VALID_INGREDIENT_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/ingredients"


def test_post_admin_ingredients_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/ingredients/new", data=VALID_INGREDIENT_FORM)
    assert db.ingredients.count == 0


def test_get_admin_ingredients_edit_returns_200_for_existing_id(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    response = admin_client.get(f"/admin/ingredients/{ingredient_id}/edit")
    assert response.status_code == 200


def test_get_admin_ingredients_edit_shows_existing_name(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    response = admin_client.get(f"/admin/ingredients/{ingredient_id}/edit")
    assert "White Beeswax" in response.text


def test_get_admin_ingredients_edit_returns_404_for_unknown_id(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/ingredients/999/edit")
    assert response.status_code == 404


def test_post_admin_ingredients_edit_updates_name(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    updated_form = {**VALID_INGREDIENT_FORM, "name": "Yellow Beeswax"}
    admin_client.post(f"/admin/ingredients/{ingredient_id}/edit", data=updated_form)
    assert db.ingredients.get(ingredient_id).name == "Yellow Beeswax"


def test_post_admin_ingredients_edit_redirects_to_admin_ingredients(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    response = admin_client.post(
        f"/admin/ingredients/{ingredient_id}/edit",
        data=VALID_INGREDIENT_FORM,
        follow_redirects=False,
    )
    assert response.headers["location"] == "/admin/ingredients"


def test_post_admin_ingredients_delete_removes_ingredient(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    admin_client.post(f"/admin/ingredients/{ingredient_id}/delete")
    assert db.ingredients.count == 0


def test_post_admin_ingredients_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    client.post(f"/admin/ingredients/{ingredient_id}/delete")
    assert db.ingredients.count == 1


def test_creating_ingredient_is_logged(
    admin_client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.INFO)
    admin_client.post("/admin/ingredients/new", data=VALID_INGREDIENT_FORM)
    assert "white beeswax" in caplog.text.lower()


def test_deleting_ingredient_is_logged(
    admin_client: TestClient, db: Database, caplog: "LogCaptureFixture"
) -> None:
    ingredient_id = _insert_ingredient(db)
    caplog.set_level(logging.WARNING)
    admin_client.post(f"/admin/ingredients/{ingredient_id}/delete")
    assert "white beeswax" in caplog.text.lower()
