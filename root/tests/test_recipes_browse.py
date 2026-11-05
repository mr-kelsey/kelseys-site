from starlette.testclient import TestClient

from app.db import Database
from app.models import Ingredient, Recipe, RecipeIngredient


def _insert_recipe(db: Database, name: str = "Tomato Soup", servings: int = 4) -> Recipe:
    return db.recipes.insert(Recipe(name=name, servings=servings, instructions="Simmer."))


def _insert_ingredient(db: Database, name: str = "Tomato") -> Ingredient:
    return db.ingredients.insert(Ingredient(name=name))


def test_get_recipes_lists_all_recipes_by_default(client: TestClient, db: Database) -> None:
    _insert_recipe(db, name="Tomato Soup")
    _insert_recipe(db, name="Plain Rice")
    response = client.get("/recipes")
    assert "Tomato Soup" in response.text and "Plain Rice" in response.text


def test_get_recipes_results_filters_by_name(client: TestClient, db: Database) -> None:
    _insert_recipe(db, name="Tomato Soup")
    _insert_recipe(db, name="Plain Rice")
    response = client.get("/recipes/results", params={"name": "tomato"})
    assert "Plain Rice" not in response.text


def test_get_recipes_results_filters_by_ingredient(client: TestClient, db: Database) -> None:
    recipe = _insert_recipe(db, name="Tomato Soup")
    ingredient = _insert_ingredient(db, name="Tomato")
    db.recipe_ingredients.insert(RecipeIngredient(recipe_id=recipe.id, ingredient_id=ingredient.id))
    _insert_recipe(db, name="Plain Rice")
    response = client.get("/recipes/results", params={"ingredient_id": ingredient.id})
    assert "Plain Rice" not in response.text


def test_get_recipes_results_filters_by_servings(client: TestClient, db: Database) -> None:
    _insert_recipe(db, name="Small Batch", servings=2)
    _insert_recipe(db, name="Big Batch", servings=8)
    response = client.get("/recipes/results", params={"servings": 2})
    assert "Big Batch" not in response.text


def test_get_recipes_results_narrows_by_trie_query_on_top_of_filters(
    client: TestClient, db: Database
) -> None:
    _insert_recipe(db, name="Tomato Soup")
    _insert_recipe(db, name="Tomato Salad")
    response = client.get("/recipes/results", params={"q": "soup"})
    assert "Tomato Salad" not in response.text


def test_get_recipe_detail_returns_200_for_existing_id(client: TestClient, db: Database) -> None:
    recipe = _insert_recipe(db)
    response = client.get(f"/recipes/{recipe.id}")
    assert response.status_code == 200


def test_get_recipe_detail_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/recipes/999")
    assert response.status_code == 404
