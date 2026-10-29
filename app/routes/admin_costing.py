from logging import getLogger

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.costing import cost_ingredients, cost_packaging, grams_needed_for_batch, minimum_restock_cost, summarize_batch_cost
from app.db import site_db
from app.models import Packaging

router = Fast.APIRouter()
logger = getLogger(__name__)

PACKAGING_ROW_COUNT = 8


def _packaging_options(packaging_items: list[Packaging]) -> list[Fast.Option]:
    return [Fast.Option("— none —", value="")] + [
        Fast.Option(item.name, value=str(item.id)) for item in packaging_items
    ]


def _packaging_rows(packaging_items: list[Packaging]) -> list[Fast.Div]:
    options = _packaging_options(packaging_items)
    return [
        Fast.Div(
            Fast.Select(*options, name="packaging_id"),
            Fast.Input(name="packaging_quantity", type="number", placeholder="Qty for this batch"),
            cls="packaging-row",
        )
        for _ in range(PACKAGING_ROW_COUNT)
    ]


def _cost_form(formula_id: int, packaging_items: list[Packaging]) -> Fast.Form:
    return Fast.Form(
        Fast.P("Enter exactly one of the two fields below."),
        Fast.Label("Number of finished units", Fast.Input(name="unit_count", type="number")),
        Fast.Label("Or target grams of output", Fast.Input(name="target_grams", type="number", step="any")),
        Fast.P("Packaging needed for this batch (optional):"),
        *_packaging_rows(packaging_items),
        Fast.Button("Calculate", type="submit"),
        method="post",
        action=f"/admin/formulas/{formula_id}/cost",
    )


@router("/admin/formulas/{formula_id}/cost")
def get(formula_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        formula = site_db.formulas.get(formula_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    packaging_items = site_db.packaging(order_by="name")
    return admin_layout(
        f"Cost {formula.name}",
        Fast.H1(f"Cost {formula.name}"),
        _cost_form(formula_id, packaging_items),
    )


@router("/admin/formulas/{formula_id}/cost")
async def post(formula_id: int, session, request):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        formula = site_db.formulas.get(formula_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)

    form = await request.form()
    packaging_items = site_db.packaging(order_by="name")

    raw_unit_count = form.get("unit_count") or ""
    raw_target_grams = form.get("target_grams") or ""
    unit_count = int(raw_unit_count) if raw_unit_count else None
    target_grams = float(raw_target_grams) if raw_target_grams else None

    links = site_db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    formula_ingredients_with_percent = [(link.ingredient_id, link.percent) for link in links]

    try:
        grams_by_ingredient_id = grams_needed_for_batch(
            formula, formula_ingredients_with_percent, unit_count=unit_count, target_grams=target_grams
        )
    except ValueError as error:
        return admin_layout(
            f"Cost {formula.name}",
            Fast.H1(f"Cost {formula.name}"),
            Fast.P(str(error), cls="error"),
            _cost_form(formula_id, packaging_items),
        )

    ingredients_by_id = {
        ingredient_id: site_db.ingredients.get(ingredient_id)
        for ingredient_id in grams_by_ingredient_id
    }
    ingredient_costs = cost_ingredients(grams_by_ingredient_id, ingredients_by_id)

    quantity_by_packaging_id: dict[int, int] = {}
    for raw_packaging_id, raw_quantity in zip(
        form.getlist("packaging_id"), form.getlist("packaging_quantity")
    ):
        if not raw_packaging_id or not raw_quantity:
            continue
        quantity_by_packaging_id[int(raw_packaging_id)] = int(raw_quantity)

    packaging_by_id = {
        packaging_id: site_db.packaging.get(packaging_id)
        for packaging_id in quantity_by_packaging_id
    }
    packaging_costs = cost_packaging(quantity_by_packaging_id, packaging_by_id)
    summary = summarize_batch_cost(ingredient_costs, packaging_costs)

    logger.info("Costed formula %r", formula.name)

    return admin_layout(
        f"Cost {formula.name}",
        Fast.H1(f"Cost {formula.name}"),
        Fast.Ul(
            *(
                Fast.Li(f"{ingredients_by_id[ingredient_id].name}: ${round(cost, 2)}")
                for ingredient_id, cost in ingredient_costs.items()
            ),
        ),
        Fast.Ul(
            *(
                Fast.Li(
                    f"{packaging_by_id[packaging_id].name}: ${round(cost, 2)} "
                    f"(restocking requires a ${round(minimum_restock_cost(packaging_by_id[packaging_id]), 2)} minimum order)"
                )
                for packaging_id, cost in packaging_costs.items()
            ),
        ),
        Fast.P(f"Ingredient total: ${round(summary['ingredient_total'], 2)}"),
        Fast.P(f"Packaging total: ${round(summary['packaging_total'], 2)}"),
        Fast.P(f"Grand total: ${round(summary['grand_total'], 2)}", cls="lede"),
        _cost_form(formula_id, packaging_items),
    )
