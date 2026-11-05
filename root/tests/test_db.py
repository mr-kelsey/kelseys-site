from apsw import ConstraintError
from pytest import raises

from app.models import Ingredient, Recipe, RecipeIngredient


def _make_recipe(db, name="Soup", servings=4):
    return db.recipes.insert(Recipe(name=name, servings=servings))


def _make_ingredient(db, name="Salt"):
    return db.ingredients.insert(Ingredient(name=name))


def _link(db, recipe, ingredient, quantity="1 cup"):
    db.recipe_ingredients.insert(
        RecipeIngredient(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=quantity)
    )


def test_filtered_recipes_matches_name_substring_case_insensitively(db):
    _make_recipe(db, name="Tomato Soup")
    results = db.filtered_recipes(name="tomato")
    assert [r.name for r in results] == ["Tomato Soup"]


def test_filtered_recipes_matches_exact_servings(db):
    _make_recipe(db, name="Small Batch", servings=2)
    _make_recipe(db, name="Big Batch", servings=8)
    results = db.filtered_recipes(servings=2)
    assert [r.name for r in results] == ["Small Batch"]


def test_filtered_recipes_matches_recipes_containing_ingredient(db):
    recipe = _make_recipe(db, name="Tomato Soup")
    ingredient = _make_ingredient(db, name="Tomato")
    _link(db, recipe, ingredient)
    _make_recipe(db, name="Plain Rice")
    results = db.filtered_recipes(ingredient_id=ingredient.id)
    assert [r.name for r in results] == ["Tomato Soup"]


def test_filtered_recipes_excludes_recipes_containing_excluded_ingredient(db):
    recipe = _make_recipe(db, name="Tomato Soup")
    ingredient = _make_ingredient(db, name="Tomato")
    _link(db, recipe, ingredient)
    _make_recipe(db, name="Plain Rice")
    results = db.filtered_recipes(excluded_ingredient_ids=(ingredient.id,))
    assert [r.name for r in results] == ["Plain Rice"]


def test_filtered_recipes_combines_name_and_ingredient_and_servings_filters(db):
    recipe = _make_recipe(db, name="Tomato Soup", servings=4)
    ingredient = _make_ingredient(db, name="Tomato")
    _link(db, recipe, ingredient)
    _make_recipe(db, name="Tomato Salad", servings=2)
    results = db.filtered_recipes(name="tomato", ingredient_id=ingredient.id, servings=4)
    assert [r.name for r in results] == ["Tomato Soup"]


def test_ingredients_name_unique_index_rejects_duplicate_insert(db):
    _make_ingredient(db, name="Butter")
    with raises(ConstraintError):
        _make_ingredient(db, name="Butter")
