from datetime import datetime, timezone
from logging import getLogger

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.db import site_db
from app.models import Ingredient, Recipe, RecipeIngredient

router = Fast.APIRouter()
logger = getLogger(__name__)

RECIPE_INGREDIENT_ROW_COUNT = 20
MINIMUM_BLANK_ROWS = 5


def _admin_recipe_row(recipe: Recipe) -> Fast.Li:
    return Fast.Li(
        Fast.Span(recipe.name, cls="row-title"),
        Fast.A("Edit", href=f"/admin/recipes/{recipe.id}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/recipes/{recipe.id}/delete",
        ),
        cls="admin-row",
    )


def _recipe_ingredient_row(ingredients: list[Ingredient], ingredient_id="", quantity="") -> Fast.Div:
    options = [Fast.Option("— none —", value="")] + [
        Fast.Option(
            ingredient.name,
            value=str(ingredient.id),
            selected=(str(ingredient.id) == str(ingredient_id)),
        )
        for ingredient in ingredients
    ]
    return Fast.Div(
        Fast.Select(*options, name="ingredient_id"),
        Fast.Input(name="quantity", placeholder='Quantity, e.g. "1 1/2 cups"', value=quantity),
        cls="recipe-ingredient-row",
    )


def _recipe_ingredient_rows(
    ingredients: list[Ingredient], existing: list[RecipeIngredient] = ()
) -> list[Fast.Div]:
    "Pre-fills a row per existing (ingredient, quantity) pair, then pads with blank rows to add more."
    rows = [
        _recipe_ingredient_row(ingredients, ingredient_id=entry.ingredient_id, quantity=entry.quantity)
        for entry in existing
    ]
    blank_count = max(RECIPE_INGREDIENT_ROW_COUNT - len(rows), MINIMUM_BLANK_ROWS)
    rows += [_recipe_ingredient_row(ingredients) for _ in range(blank_count)]
    return rows


def _recipe_form(
    ingredients: list[Ingredient],
    recipe: Recipe | None = None,
    existing_ingredients: list[RecipeIngredient] = (),
    *,
    action: str,
) -> Fast.Form:
    recipe = recipe or Recipe()
    return Fast.Form(
        Fast.Label("Name", Fast.Input(name="name", value=recipe.name, required=True)),
        Fast.Label(
            "Servings",
            Fast.Input(name="servings", type="number", min="1", value=recipe.servings, required=True),
        ),
        Fast.Label(
            "Instructions", Fast.Textarea(recipe.instructions, name="instructions", required=True)
        ),
        Fast.Label("Notes", Fast.Textarea(recipe.notes, name="notes")),
        Fast.P("Ingredients — leave a row blank to skip it."),
        *_recipe_ingredient_rows(ingredients, existing_ingredients),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


def _submitted_ingredient_rows(form) -> list[tuple[int, str]]:
    "Returns (ingredient_id, quantity) for every row where both fields were filled in."
    rows = []
    for raw_ingredient_id, quantity in zip(form.getlist("ingredient_id"), form.getlist("quantity")):
        quantity = quantity.strip()
        if raw_ingredient_id and quantity:
            rows.append((int(raw_ingredient_id), quantity))
    return rows


def _replace_recipe_ingredients(recipe_id: int, rows: list[tuple[int, str]]) -> None:
    site_db.recipe_ingredients.delete_where("recipe_id = ?", [recipe_id])
    for ingredient_id, quantity in rows:
        site_db.recipe_ingredients.insert(
            RecipeIngredient(recipe_id=recipe_id, ingredient_id=ingredient_id, quantity=quantity)
        )


@router("/admin/recipes")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    recipes = site_db.recipes(order_by="name")
    return admin_layout(
        "Manage Recipes",
        Fast.H1("Manage Recipes"),
        Fast.Div(Fast.A("New Recipe", href="/admin/recipes/new"), cls="admin-action"),
        Fast.Ul(*(_admin_recipe_row(recipe) for recipe in recipes), cls="admin-list"),
    )


@router("/admin/recipes/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    ingredients = site_db.ingredients(order_by="name")
    return admin_layout(
        "New Recipe",
        Fast.H1("New Recipe"),
        _recipe_form(ingredients, action="/admin/recipes/new"),
    )


@router("/admin/recipes/new")
async def post(session, request):
    if (redirect := require_admin(session)) is not None:
        return redirect
    form = await request.form()
    recipe = site_db.recipes.insert(
        Recipe(
            name=form["name"],
            servings=int(form["servings"]),
            instructions=form["instructions"],
            notes=form.get("notes", ""),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    _replace_recipe_ingredients(recipe.id, _submitted_ingredient_rows(form))
    logger.info("Created recipe %r", recipe.name)
    return Fast.Redirect(f"/admin/recipes/{recipe.id}/edit")


@router("/admin/recipes/{recipe_id}/edit")
def get(recipe_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        recipe = site_db.recipes.get(recipe_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    ingredients = site_db.ingredients(order_by="name")
    existing = site_db.recipe_ingredients(where="recipe_id = ?", where_args=[recipe_id])
    return admin_layout(
        "Edit Recipe",
        Fast.H1("Edit Recipe"),
        _recipe_form(
            ingredients, recipe, existing, action=f"/admin/recipes/{recipe_id}/edit"
        ),
    )


@router("/admin/recipes/{recipe_id}/edit")
async def post(recipe_id: int, session, request):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.recipes.get(recipe_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    form = await request.form()
    site_db.recipes.update(
        {
            "id": recipe_id,
            "name": form["name"],
            "servings": int(form["servings"]),
            "instructions": form["instructions"],
            "notes": form.get("notes", ""),
        }
    )
    _replace_recipe_ingredients(recipe_id, _submitted_ingredient_rows(form))
    logger.info("Updated recipe %r", form["name"])
    return Fast.Redirect(f"/admin/recipes/{recipe_id}/edit")


@router("/admin/recipes/{recipe_id}/delete")
def post(recipe_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        recipe = site_db.recipes.get(recipe_id)
    except NotFoundError:
        return Fast.Redirect("/admin/recipes")
    site_db.recipe_ingredients.delete_where("recipe_id = ?", [recipe_id])
    site_db.recipes.delete(recipe_id)
    logger.warning("Deleted recipe %r", recipe.name)
    return Fast.Redirect("/admin/recipes")
