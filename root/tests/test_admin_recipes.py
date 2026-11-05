from starlette.testclient import TestClient

from app.db import Database
from app.models import Ingredient, Recipe, RecipeIngredient

VALID_RECIPE_FORM = {
    "name": "Tomato Soup",
    "servings": "4",
    "instructions": "Simmer everything for 20 minutes.",
    "notes": "",
}


def _insert_recipe(db: Database, name: str = "Tomato Soup") -> int:
    return db.recipes.insert(Recipe(name=name, servings=4, instructions="Simmer.")).id


def _insert_ingredient(db: Database, name: str = "Tomato") -> int:
    return db.ingredients.insert(Ingredient(name=name)).id


def test_get_admin_recipes_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/recipes", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_recipes_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/recipes")
    assert response.status_code == 200


def test_get_admin_recipes_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/recipes/new")
    assert response.status_code == 200


def test_post_admin_recipes_new_creates_recipe(admin_client: TestClient, db: Database) -> None:
    admin_client.post("/admin/recipes/new", data=VALID_RECIPE_FORM)
    assert db.recipes.count == 1


def test_post_admin_recipes_new_creates_recipe_with_ingredients(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    form = {**VALID_RECIPE_FORM, "ingredient_id": [str(ingredient_id)], "quantity": ["2 cans"]}
    admin_client.post("/admin/recipes/new", data=form)
    assert db.recipe_ingredients.count == 1


def test_post_admin_recipes_new_skips_rows_left_blank(
    admin_client: TestClient, db: Database
) -> None:
    ingredient_id = _insert_ingredient(db)
    form = {**VALID_RECIPE_FORM, "ingredient_id": [str(ingredient_id), ""], "quantity": ["2 cans", ""]}
    admin_client.post("/admin/recipes/new", data=form)
    assert db.recipe_ingredients.count == 1


def test_post_admin_recipes_new_redirects_to_edit_page(admin_client: TestClient, db: Database) -> None:
    response = admin_client.post(
        "/admin/recipes/new", data=VALID_RECIPE_FORM, follow_redirects=False
    )
    recipe_id = db.recipes(order_by="id")[0].id
    assert response.headers["location"] == f"/admin/recipes/{recipe_id}/edit"


def test_post_admin_recipes_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/recipes/new", data=VALID_RECIPE_FORM)
    assert db.recipes.count == 0


def test_get_admin_recipes_edit_returns_200_for_existing_id(
    admin_client: TestClient, db: Database
) -> None:
    recipe_id = _insert_recipe(db)
    response = admin_client.get(f"/admin/recipes/{recipe_id}/edit")
    assert response.status_code == 200


def test_get_admin_recipes_edit_returns_404_for_unknown_id(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/recipes/999/edit")
    assert response.status_code == 404


def test_get_admin_recipes_edit_prefills_existing_ingredient_rows(
    admin_client: TestClient, db: Database
) -> None:
    recipe_id = _insert_recipe(db)
    ingredient_id = _insert_ingredient(db)
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_id, ingredient_id=ingredient_id, quantity="2 cans")
    )
    response = admin_client.get(f"/admin/recipes/{recipe_id}/edit")
    assert "2 cans" in response.text


def test_post_admin_recipes_edit_updates_name(admin_client: TestClient, db: Database) -> None:
    recipe_id = _insert_recipe(db)
    form = {**VALID_RECIPE_FORM, "name": "Tomato Bisque"}
    admin_client.post(f"/admin/recipes/{recipe_id}/edit", data=form)
    assert db.recipes.get(recipe_id).name == "Tomato Bisque"


def test_post_admin_recipes_edit_replaces_ingredient_list(
    admin_client: TestClient, db: Database
) -> None:
    recipe_id = _insert_recipe(db)
    first_ingredient_id = _insert_ingredient(db, name="Tomato")
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_id, ingredient_id=first_ingredient_id, quantity="2 cans")
    )
    second_ingredient_id = _insert_ingredient(db, name="Basil")
    form = {
        **VALID_RECIPE_FORM,
        "ingredient_id": [str(second_ingredient_id)],
        "quantity": ["a handful"],
    }
    admin_client.post(f"/admin/recipes/{recipe_id}/edit", data=form)
    remaining = db.recipe_ingredients(where="recipe_id = ?", where_args=[recipe_id])
    assert [row.ingredient_id for row in remaining] == [second_ingredient_id]


def test_post_admin_recipes_edit_removes_ingredient_left_blank(
    admin_client: TestClient, db: Database
) -> None:
    recipe_id = _insert_recipe(db)
    ingredient_id = _insert_ingredient(db)
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_id, ingredient_id=ingredient_id, quantity="2 cans")
    )
    admin_client.post(f"/admin/recipes/{recipe_id}/edit", data=VALID_RECIPE_FORM)
    assert db.recipe_ingredients.count == 0


def test_post_admin_recipes_delete_removes_recipe(admin_client: TestClient, db: Database) -> None:
    recipe_id = _insert_recipe(db)
    admin_client.post(f"/admin/recipes/{recipe_id}/delete")
    assert db.recipes.count == 0


def test_post_admin_recipes_delete_removes_recipe_ingredients_too(
    admin_client: TestClient, db: Database
) -> None:
    recipe_id = _insert_recipe(db)
    ingredient_id = _insert_ingredient(db)
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_id, ingredient_id=ingredient_id, quantity="2 cans")
    )
    admin_client.post(f"/admin/recipes/{recipe_id}/delete")
    assert db.recipe_ingredients.count == 0


def test_post_admin_recipes_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    recipe_id = _insert_recipe(db)
    client.post(f"/admin/recipes/{recipe_id}/delete")
    assert db.recipes.count == 1
