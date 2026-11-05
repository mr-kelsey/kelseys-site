from datetime import datetime, timezone
from logging import getLogger

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.costing import convert_recipe_to_percentages
from app.db import site_db
from app.models import Formula, FormulaIngredient, Ingredient

router = Fast.APIRouter()
logger = getLogger(__name__)

RECIPE_ROW_COUNT = 12


def _admin_formula_row(formula: Formula) -> Fast.Li:
    return Fast.Li(
        Fast.Span(formula.name, cls="row-title"),
        Fast.A("View", href=f"/admin/formulas/{formula.id}"),
        Fast.A("Edit", href=f"/admin/formulas/{formula.id}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/formulas/{formula.id}/delete",
        ),
        cls="admin-row",
    )


def _formula_shell_form(formula: Formula | None = None, *, action: str) -> Fast.Form:
    formula = formula or Formula()
    return Fast.Form(
        Fast.Label("Name", Fast.Input(name="name", value=formula.name, required=True)),
        Fast.Label(
            "Grams yielded per unit",
            Fast.Input(
                name="grams_per_unit",
                type="number",
                step="any",
                value=formula.grams_per_unit,
                required=True,
            ),
        ),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


def _recipe_editor_rows(ingredients: list[Ingredient]) -> list[Fast.Div]:
    """Fixed-count blank rows for entering a formula's recipe in raw
    purchase units — not pre-populated with the formula's existing
    ingredients, since only the derived percent is stored, not the raw
    quantity that produced it. Leaving every row blank on save keeps the
    existing recipe untouched (see the edit POST handler); submitting any
    filled rows replaces the whole stored recipe at once."""
    options = [Fast.Option("— none —", value="")] + [
        Fast.Option(ingredient.name, value=str(ingredient.id)) for ingredient in ingredients
    ]
    return [
        Fast.Div(
            Fast.Select(*options, name="ingredient_id"),
            Fast.Input(
                name="quantity", type="number", step="any", placeholder="Qty in its own unit"
            ),
            cls="recipe-row",
        )
        for _ in range(RECIPE_ROW_COUNT)
    ]


@router("/admin/formulas")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    formulas = site_db.formulas(order_by="id")
    return admin_layout(
        "Manage Formulas",
        Fast.H1("Manage Formulas"),
        Fast.Div(Fast.A("New Formula", href="/admin/formulas/new"), cls="admin-action"),
        Fast.Ul(*(_admin_formula_row(formula) for formula in formulas), cls="admin-list"),
    )


@router("/admin/formulas/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    return admin_layout(
        "New Formula",
        Fast.H1("New Formula"),
        _formula_shell_form(action="/admin/formulas/new"),
    )


@router("/admin/formulas/new")
def post(session, name: str, grams_per_unit: float):
    if (redirect := require_admin(session)) is not None:
        return redirect
    inserted = site_db.formulas.insert(
        Formula(
            name=name,
            grams_per_unit=grams_per_unit,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    logger.info("Created formula %r", name)
    return Fast.Redirect(f"/admin/formulas/{inserted.id}/edit")


@router("/admin/formulas/{formula_id}")
def get(formula_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        formula = site_db.formulas.get(formula_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    links = site_db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    rows = []
    for link in links:
        try:
            ingredient = site_db.ingredients.get(link.ingredient_id)
        except NotFoundError:
            continue
        rows.append(Fast.Li(f"{ingredient.name}: {round(link.percent, 2)}%"))
    return admin_layout(
        formula.name,
        Fast.H1(formula.name),
        Fast.P(f"Yields {formula.grams_per_unit}g per unit"),
        Fast.Ul(*rows),
        Fast.Div(
            Fast.A("Cost this out", href=f"/admin/formulas/{formula_id}/cost"),
            Fast.A("Edit", href=f"/admin/formulas/{formula_id}/edit"),
            cls="admin-action",
        ),
    )


@router("/admin/formulas/{formula_id}/edit")
def get(formula_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        formula = site_db.formulas.get(formula_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    ingredients = site_db.ingredients(order_by="name")
    return admin_layout(
        "Edit Formula",
        Fast.H1("Edit Formula"),
        Fast.Form(
            Fast.Label("Name", Fast.Input(name="name", value=formula.name, required=True)),
            Fast.Label(
                "Grams yielded per unit",
                Fast.Input(
                    name="grams_per_unit",
                    type="number",
                    step="any",
                    value=formula.grams_per_unit,
                    required=True,
                ),
            ),
            Fast.P(
                "Recipe — enter each ingredient's quantity in its own purchase unit. "
                "Leave every row blank to keep the current recipe unchanged; filling in "
                "any rows replaces the whole stored recipe with the new percentages."
            ),
            *_recipe_editor_rows(ingredients),
            Fast.Button("Save", type="submit"),
            method="post",
            action=f"/admin/formulas/{formula_id}/edit",
        ),
    )


@router("/admin/formulas/{formula_id}/edit")
async def post(formula_id: int, session, request):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.formulas.get(formula_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)

    form = await request.form()
    name = form["name"]
    grams_per_unit = float(form["grams_per_unit"])

    entries: list[tuple[Ingredient, float]] = []
    for raw_ingredient_id, raw_quantity in zip(
        form.getlist("ingredient_id"), form.getlist("quantity")
    ):
        if not raw_ingredient_id or not raw_quantity:
            continue
        try:
            ingredient = site_db.ingredients.get(int(raw_ingredient_id))
        except NotFoundError:
            continue
        entries.append((ingredient, float(raw_quantity)))

    site_db.formulas.update(
        {"id": formula_id, "name": name, "grams_per_unit": grams_per_unit}
    )

    if entries:
        for link in site_db.formula_ingredients(
            where="formula_id=?", where_args=[formula_id]
        ):
            site_db.formula_ingredients.delete(link.id)
        for ingredient, percent in convert_recipe_to_percentages(entries):
            site_db.formula_ingredients.insert(
                FormulaIngredient(
                    formula_id=formula_id, ingredient_id=ingredient.id, percent=percent
                )
            )

    logger.info("Updated formula %r", name)
    return Fast.Redirect(f"/admin/formulas/{formula_id}")


@router("/admin/formulas/{formula_id}/delete")
def post(formula_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        formula = site_db.formulas.get(formula_id)
    except NotFoundError:
        return Fast.Redirect("/admin/formulas")
    for link in site_db.formula_ingredients(where="formula_id=?", where_args=[formula_id]):
        site_db.formula_ingredients.delete(link.id)
    site_db.formulas.delete(formula_id)
    logger.warning("Deleted formula %r", formula.name)
    return Fast.Redirect("/admin/formulas")
