from datetime import datetime, timezone
from logging import getLogger

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.db import site_db
from app.models import Ingredient

router = Fast.APIRouter()
logger = getLogger(__name__)


def _admin_ingredient_row(ingredient: Ingredient) -> Fast.Li:
    return Fast.Li(
        Fast.Span(ingredient.name, cls="row-title"),
        Fast.A("Edit", href=f"/admin/ingredients/{ingredient.id}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/ingredients/{ingredient.id}/delete",
        ),
        cls="admin-row",
    )


def _ingredient_form(
    ingredient: Ingredient | None = None, *, action: str, error: str | None = None
) -> Fast.Form:
    ingredient = ingredient or Ingredient()
    return Fast.Form(
        Fast.P(error, cls="error") if error else None,
        Fast.Label("Name", Fast.Input(name="name", value=ingredient.name, required=True)),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


def _name_already_used(name: str, *, excluding_id: int | None = None) -> bool:
    matches = site_db.ingredients(where="name = ? COLLATE NOCASE", where_args=[name])
    return any(match.id != excluding_id for match in matches)


def _recipe_ids_using(ingredient_id: int) -> list[int]:
    rows = site_db.connection.q(
        "SELECT DISTINCT recipe_id FROM recipe_ingredients WHERE ingredient_id = :ingredient_id",
        {"ingredient_id": ingredient_id},
    )
    return [row["recipe_id"] for row in rows]


@router("/admin/ingredients")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    ingredients = site_db.ingredients(order_by="name")
    return admin_layout(
        "Manage Ingredients",
        Fast.H1("Manage Ingredients"),
        Fast.Div(Fast.A("New Ingredient", href="/admin/ingredients/new"), cls="admin-action"),
        Fast.Ul(*(_admin_ingredient_row(ingredient) for ingredient in ingredients), cls="admin-list"),
    )


@router("/admin/ingredients/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    return admin_layout(
        "New Ingredient",
        Fast.H1("New Ingredient"),
        _ingredient_form(action="/admin/ingredients/new"),
    )


@router("/admin/ingredients/new")
def post(session, name: str):
    if (redirect := require_admin(session)) is not None:
        return redirect
    name = name.strip()
    if _name_already_used(name):
        return admin_layout(
            "New Ingredient",
            Fast.H1("New Ingredient"),
            _ingredient_form(
                Ingredient(name=name),
                action="/admin/ingredients/new",
                error=f'"{name}" already exists.',
            ),
        )
    site_db.ingredients.insert(Ingredient(name=name, created_at=datetime.now(timezone.utc).isoformat()))
    logger.info("Created ingredient %r", name)
    return Fast.Redirect("/admin/ingredients")


@router("/admin/ingredients/{ingredient_id}/edit")
def get(ingredient_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        ingredient = site_db.ingredients.get(ingredient_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    return admin_layout(
        "Edit Ingredient",
        Fast.H1("Edit Ingredient"),
        _ingredient_form(ingredient, action=f"/admin/ingredients/{ingredient_id}/edit"),
    )


@router("/admin/ingredients/{ingredient_id}/edit")
def post(ingredient_id: int, session, name: str):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.ingredients.get(ingredient_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    name = name.strip()
    if _name_already_used(name, excluding_id=ingredient_id):
        return admin_layout(
            "Edit Ingredient",
            Fast.H1("Edit Ingredient"),
            _ingredient_form(
                Ingredient(id=ingredient_id, name=name),
                action=f"/admin/ingredients/{ingredient_id}/edit",
                error=f'"{name}" already exists.',
            ),
        )
    site_db.ingredients.update({"id": ingredient_id, "name": name})
    logger.info("Updated ingredient %r", name)
    return Fast.Redirect("/admin/ingredients")


@router("/admin/ingredients/{ingredient_id}/delete")
def post(ingredient_id: int, session, confirm: str = ""):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        ingredient = site_db.ingredients.get(ingredient_id)
    except NotFoundError:
        return Fast.Redirect("/admin/ingredients")
    recipe_ids = _recipe_ids_using(ingredient_id)
    if recipe_ids and confirm != "1":
        recipe_names = [site_db.recipes.get(recipe_id).name for recipe_id in recipe_ids]
        return admin_layout(
            "Delete Ingredient",
            Fast.H1("Delete Ingredient"),
            Fast.P(
                f'"{ingredient.name}" is used in {len(recipe_ids)} recipe(s): '
                f'{", ".join(recipe_names)}.'
            ),
            Fast.P("Deleting it will remove it from those recipes."),
            Fast.Form(
                Fast.Input(type="hidden", name="confirm", value="1"),
                Fast.Button("Delete anyway", type="submit"),
                method="post",
                action=f"/admin/ingredients/{ingredient_id}/delete",
            ),
        )
    site_db.recipe_ingredients.delete_where("ingredient_id = ?", [ingredient_id])
    site_db.ingredients.delete(ingredient_id)
    logger.warning("Deleted ingredient %r", ingredient.name)
    return Fast.Redirect("/admin/ingredients")
