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


def _ingredient_form(ingredient: Ingredient | None = None, *, action: str) -> Fast.Form:
    ingredient = ingredient or Ingredient()
    return Fast.Form(
        Fast.Label("Name", Fast.Input(name="name", value=ingredient.name, required=True)),
        Fast.Label("Vendor", Fast.Input(name="vendor", value=ingredient.vendor)),
        Fast.Label(
            "Purchase volume",
            Fast.Input(
                name="purchase_volume",
                type="number",
                step="any",
                value=ingredient.purchase_volume,
                required=True,
            ),
        ),
        Fast.Label("Volume unit", Fast.Input(name="volume_unit", value=ingredient.volume_unit)),
        Fast.Label(
            "Total grams",
            Fast.Input(
                name="total_grams",
                type="number",
                step="any",
                value=ingredient.total_grams,
                required=True,
            ),
        ),
        Fast.Label(
            "Purchase price",
            Fast.Input(
                name="purchase_price",
                type="number",
                step="any",
                value=ingredient.purchase_price,
                required=True,
            ),
        ),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


@router("/admin/ingredients")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    ingredients = site_db.ingredients(order_by="id")
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
def post(
    session,
    name: str,
    purchase_volume: float,
    total_grams: float,
    purchase_price: float,
    vendor: str = "",
    volume_unit: str = "",
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    site_db.ingredients.insert(
        Ingredient(
            name=name,
            vendor=vendor,
            purchase_volume=purchase_volume,
            volume_unit=volume_unit,
            total_grams=total_grams,
            purchase_price=purchase_price,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
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
def post(
    ingredient_id: int,
    session,
    name: str,
    purchase_volume: float,
    total_grams: float,
    purchase_price: float,
    vendor: str = "",
    volume_unit: str = "",
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.ingredients.get(ingredient_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    site_db.ingredients.update(
        {
            "id": ingredient_id,
            "name": name,
            "vendor": vendor,
            "purchase_volume": purchase_volume,
            "volume_unit": volume_unit,
            "total_grams": total_grams,
            "purchase_price": purchase_price,
        }
    )
    logger.info("Updated ingredient %r", name)
    return Fast.Redirect("/admin/ingredients")


@router("/admin/ingredients/{ingredient_id}/delete")
def post(ingredient_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        ingredient = site_db.ingredients.get(ingredient_id)
    except NotFoundError:
        return Fast.Redirect("/admin/ingredients")
    site_db.ingredients.delete(ingredient_id)
    logger.warning("Deleted ingredient %r", ingredient.name)
    return Fast.Redirect("/admin/ingredients")
