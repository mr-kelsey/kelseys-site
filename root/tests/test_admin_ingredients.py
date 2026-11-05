from starlette.testclient import TestClient

from app.db import Database
from app.models import Ingredient, Recipe, RecipeIngredient

VALID_INGREDIENT_FORM = {"name": "White Beeswax"}


def _insert_ingredient(db: Database, name: str = "White Beeswax") -> int:
    return db.ingredients.insert(Ingredient(name=name)).id


def test_get_admin_ingredients_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/ingredients", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_ingredients_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/ingredients")
    assert response.status_code == 200


def test_get_admin_ingredients_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/ingredients/new")
    assert response.status_code == 200


def test_post_admin_ingredients_new_creates_ingredient(admin_client: TestClient, db: Database) -> None:
    admin_client.post("/admin/ingredients/new", data=VALID_INGREDIENT_FORM)
    assert db.ingredients.count == 1


def test_post_admin_ingredients_new_redirects_to_admin_ingredients(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/admin/ingredients/new", data=VALID_INGREDIENT_FORM, follow_redirects=False
    )
    assert response.headers["location"] == "/admin/ingredients"


def test_post_admin_ingredients_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/ingredients/new", data=VALID_INGREDIENT_FORM)
    assert db.ingredients.count == 0


def test_post_admin_ingredients_new_rejects_case_insensitive_duplicate_name(
    admin_client: TestClient, db: Database
) -> None:
    _insert_ingredient(db, name="Butter")
    admin_client.post("/admin/ingredients/new", data={"name": "butter"})
    assert db.ingredients.count == 1


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


def test_get_admin_ingredients_edit_returns_404_for_unknown_id(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/ingredients/999/edit")
    assert response.status_code == 404


def test_post_admin_ingredients_edit_updates_name(admin_client: TestClient, db: Database) -> None:
    ingredient_id = _insert_ingredient(db)
    admin_client.post(f"/admin/ingredients/{ingredient_id}/edit", data={"name": "Yellow Beeswax"})
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


def test_post_admin_ingredients_delete_removes_ingredient_when_unused(
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


def test_post_admin_ingredients_delete_blocks_when_used_by_a_recipe_without_confirm(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    recipe_id = db.recipes.insert(Recipe(name="Toast")).id
    db.recipe_ingredients.insert(RecipeIngredient(recipe_id=recipe_id, ingredient_id=ingredient_id))
    admin_client.post(f"/admin/ingredients/{ingredient_id}/delete")
    assert db.ingredients.count == 1


def test_post_admin_ingredients_delete_removes_it_from_recipes_when_confirmed(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    recipe_id = db.recipes.insert(Recipe(name="Toast")).id
    db.recipe_ingredients.insert(RecipeIngredient(recipe_id=recipe_id, ingredient_id=ingredient_id))
    admin_client.post(f"/admin/ingredients/{ingredient_id}/delete", data={"confirm": "1"})
    assert db.ingredients.count == 0
