"""Formulation/costing business logic — replaces the old CLI's
convert_recepeit / get_ingredients_needed / get_product_cost /
get_weight_percentages, using real objects and ids instead of
lowercased-name string lookups.

Pure functions only; no DB or web framework coupling, so each is
independently unit-testable."""

from app.models import Formula, Ingredient, Packaging


def grams_for_quantity(ingredient: Ingredient, quantity: float) -> float:
    if ingredient.purchase_volume == 0:
        raise ValueError(f"ingredient {ingredient.name!r} has no purchase_volume set")
    return quantity * (ingredient.total_grams / ingredient.purchase_volume)


def convert_recipe_to_percentages(
    entries: list[tuple[Ingredient, float]],
) -> list[tuple[Ingredient, float]]:
    if not entries:
        raise ValueError("recipe must include at least one ingredient")
    grams_by_ingredient = [
        (ingredient, grams_for_quantity(ingredient, quantity)) for ingredient, quantity in entries
    ]
    total_grams = sum(grams for _, grams in grams_by_ingredient)
    return [(ingredient, grams * 100 / total_grams) for ingredient, grams in grams_by_ingredient]


def grams_needed_for_batch(
    formula: Formula,
    formula_ingredients_with_percent: list[tuple[int, float]],
    *,
    unit_count: int | None = None,
    target_grams: float | None = None,
) -> dict[int, float]:
    if (unit_count is None) == (target_grams is None):
        raise ValueError("exactly one of unit_count or target_grams must be provided")
    total_grams = (
        unit_count * formula.grams_per_unit if unit_count is not None else target_grams
    )
    return {
        ingredient_id: total_grams * (percent / 100)
        for ingredient_id, percent in formula_ingredients_with_percent
    }


def cost_ingredients(
    grams_by_ingredient_id: dict[int, float], ingredients_by_id: dict[int, Ingredient]
) -> dict[int, float]:
    return {
        ingredient_id: grams
        * (
            ingredients_by_id[ingredient_id].purchase_price
            / ingredients_by_id[ingredient_id].total_grams
        )
        for ingredient_id, grams in grams_by_ingredient_id.items()
    }


def cost_packaging(
    quantity_by_packaging_id: dict[int, int], packaging_by_id: dict[int, Packaging]
) -> dict[int, float]:
    return {
        packaging_id: quantity
        * (
            packaging_by_id[packaging_id].purchase_price
            / packaging_by_id[packaging_id].purchase_volume
        )
        for packaging_id, quantity in quantity_by_packaging_id.items()
    }


def summarize_batch_cost(
    ingredient_costs: dict[int, float], packaging_costs: dict[int, float]
) -> dict[str, float]:
    ingredient_total = sum(ingredient_costs.values())
    packaging_total = sum(packaging_costs.values())
    return {
        "ingredient_total": ingredient_total,
        "packaging_total": packaging_total,
        "grand_total": ingredient_total + packaging_total,
    }


def minimum_restock_cost(packaging: Packaging) -> float:
    """The cash required to place a qualifying order with the supplier at
    all — moq_for_price is a procurement constraint (minimum units the
    supplier requires to sell at purchase_price), not a customer sales
    tier, so this is independent of how much a given batch actually needs."""
    return packaging.moq_for_price * (packaging.purchase_price / packaging.purchase_volume)
