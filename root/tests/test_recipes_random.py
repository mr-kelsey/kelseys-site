from starlette.testclient import TestClient

from app.db import Database
from app.models import Ingredient, Recipe, RecipeIngredient


def _insert_recipe(db: Database, name: str = "Tomato Soup") -> Recipe:
    return db.recipes.insert(Recipe(name=name, servings=4, instructions="Simmer."))


def _insert_ingredient(db: Database, name: str = "Tomato") -> Ingredient:
    return db.ingredients.insert(Ingredient(name=name))


def test_get_recipes_random_returns_a_recipe_from_the_filtered_pool(
    client: TestClient, db: Database
) -> None:
    _insert_recipe(db, name="Tomato Soup")
    response = client.get("/recipes/random")
    assert "Tomato Soup" in response.text


def test_get_recipes_random_excludes_recipes_with_excluded_ingredient(
    client: TestClient, db: Database
) -> None:
    tomato = _insert_ingredient(db, name="Tomato")
    recipe_with_tomato = _insert_recipe(db, name="Tomato Soup")
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_with_tomato.id, ingredient_id=tomato.id)
    )
    _insert_recipe(db, name="Plain Rice")
    client.post(f"/recipes/random/exclude/{tomato.id}")
    response = client.get("/recipes/random")
    assert "Tomato Soup" not in response.text


def test_post_exclude_adds_ingredient_to_session_and_redirects(
    client: TestClient, db: Database
) -> None:
    ingredient = _insert_ingredient(db)
    response = client.post(f"/recipes/random/exclude/{ingredient.id}", follow_redirects=False)
    assert response.headers["location"].startswith("/recipes/random")


def test_post_accept_clears_excluded_ingredients_from_session(
    client: TestClient, db: Database
) -> None:
    tomato = _insert_ingredient(db, name="Tomato")
    recipe_with_tomato = _insert_recipe(db, name="Tomato Soup")
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_with_tomato.id, ingredient_id=tomato.id)
    )
    client.post(f"/recipes/random/exclude/{tomato.id}")
    client.post("/recipes/random/accept", data={"recipe_id": recipe_with_tomato.id})
    response = client.get("/recipes/random")
    assert "Tomato Soup" in response.text


def test_get_recipes_random_shows_message_when_pool_is_empty(client: TestClient) -> None:
    response = client.get("/recipes/random")
    assert "No recipes" in response.text


def test_post_reset_clears_excluded_ingredients_from_session(
    client: TestClient, db: Database
) -> None:
    tomato = _insert_ingredient(db, name="Tomato")
    recipe_with_tomato = _insert_recipe(db, name="Tomato Soup")
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe_with_tomato.id, ingredient_id=tomato.id)
    )
    client.post(f"/recipes/random/exclude/{tomato.id}")
    client.post("/recipes/random/reset")
    response = client.get("/recipes/random")
    assert "Tomato Soup" in response.text
