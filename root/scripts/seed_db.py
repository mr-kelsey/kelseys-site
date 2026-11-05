"""Bootstraps a brand-new, empty data/app.db with sample dev content so the
recipe book and calendar have something to browse locally. Not idempotent --
re-running against an already-seeded DB duplicates every row; use /admin for
edits after the initial seed."""

from app.db import site_db
from app.models import Ingredient, Recipe, RecipeIngredient

SAMPLE_INGREDIENTS = (
    "Tomato",
    "Garlic",
    "Olive Oil",
    "Basil",
    "Rice",
    "Butter",
    "Flour",
    "Sugar",
    "Eggs",
    "Cocoa Powder",
)

SAMPLE_RECIPES = (
    {
        "name": "Tomato Soup",
        "servings": 4,
        "instructions": "Simmer tomatoes with garlic and olive oil for 20 minutes. Blend and stir in basil.",
        "notes": "Good with crusty bread.",
        "ingredients": {"Tomato": "6 large", "Garlic": "2 cloves", "Olive Oil": "2 tbsp", "Basil": "a handful"},
    },
    {
        "name": "Plain Rice",
        "servings": 2,
        "instructions": "Rinse rice, simmer covered in twice its volume of water for 18 minutes.",
        "notes": "",
        "ingredients": {"Rice": "1 cup"},
    },
    {
        "name": "Chocolate Cake",
        "servings": 8,
        "instructions": "Cream butter and sugar, beat in eggs, fold in flour and cocoa powder. Bake at 350F for 30 minutes.",
        "notes": "A family favorite.",
        "ingredients": {
            "Butter": "1 cup",
            "Sugar": "2 cups",
            "Eggs": "3",
            "Flour": "2 cups",
            "Cocoa Powder": "3/4 cup",
        },
    },
)


def seed() -> None:
    ingredients_by_name = {
        name: site_db.ingredients.insert(Ingredient(name=name)) for name in SAMPLE_INGREDIENTS
    }
    for recipe_data in SAMPLE_RECIPES:
        recipe = site_db.recipes.insert(
            Recipe(
                name=recipe_data["name"],
                servings=recipe_data["servings"],
                instructions=recipe_data["instructions"],
                notes=recipe_data["notes"],
            )
        )
        for ingredient_name, quantity in recipe_data["ingredients"].items():
            site_db.recipe_ingredients.insert(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredients_by_name[ingredient_name].id,
                    quantity=quantity,
                )
            )


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(SAMPLE_RECIPES)} recipes and {len(SAMPLE_INGREDIENTS)} ingredients.")
