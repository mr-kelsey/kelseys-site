from math import isclose

from pytest import raises

from app.costing import (
    convert_recipe_to_percentages,
    cost_ingredients,
    cost_packaging,
    grams_for_quantity,
    grams_needed_for_batch,
    minimum_restock_cost,
    summarize_batch_cost,
)
from app.models import Formula, Ingredient, Packaging


def _beeswax() -> Ingredient:
    return Ingredient(
        id=1, name="White Beeswax", purchase_volume=16, total_grams=453.59, purchase_price=12
    )


def _coconut_oil() -> Ingredient:
    return Ingredient(
        id=2, name="Coconut Oil", purchase_volume=54, total_grams=1530.874, purchase_price=20
    )


def _tubes() -> Packaging:
    return Packaging(id=1, name="Lip Balm Tubes", purchase_volume=1000, purchase_price=810, moq_for_price=1000)


def test_grams_for_quantity_converts_purchase_units_to_grams() -> None:
    assert grams_for_quantity(_beeswax(), 3) == 3 * (453.59 / 16)


def test_grams_for_quantity_raises_for_zero_purchase_volume() -> None:
    with raises(ValueError):
        grams_for_quantity(Ingredient(name="Bad", purchase_volume=0), 1)


def test_convert_recipe_to_percentages_sums_to_100() -> None:
    result = convert_recipe_to_percentages([(_beeswax(), 3), (_coconut_oil(), 5)])
    assert isclose(sum(percent for _, percent in result), 100, abs_tol=1e-6)


def test_convert_recipe_to_percentages_rejects_empty_recipe() -> None:
    with raises(ValueError):
        convert_recipe_to_percentages([])


def test_grams_needed_for_batch_from_unit_count() -> None:
    formula = Formula(id=1, name="Lip Balm", grams_per_unit=10.0)
    result = grams_needed_for_batch(formula, [(1, 50.0)], unit_count=2)
    assert result[1] == 10.0


def test_grams_needed_for_batch_from_target_grams() -> None:
    formula = Formula(id=1, name="Lip Balm", grams_per_unit=10.0)
    result = grams_needed_for_batch(formula, [(1, 50.0)], target_grams=40.0)
    assert result[1] == 20.0


def test_grams_needed_for_batch_rejects_both_unit_count_and_target_grams() -> None:
    formula = Formula(id=1, name="Lip Balm", grams_per_unit=10.0)
    with raises(ValueError):
        grams_needed_for_batch(formula, [(1, 50.0)], unit_count=2, target_grams=40.0)


def test_grams_needed_for_batch_rejects_neither_unit_count_nor_target_grams() -> None:
    formula = Formula(id=1, name="Lip Balm", grams_per_unit=10.0)
    with raises(ValueError):
        grams_needed_for_batch(formula, [(1, 50.0)])


def test_cost_ingredients_computes_cost_per_ingredient() -> None:
    beeswax = _beeswax()
    result = cost_ingredients({1: 10.0}, {1: beeswax})
    assert result[1] == 10.0 * (beeswax.purchase_price / beeswax.total_grams)


def test_cost_packaging_computes_cost_per_packaging_item() -> None:
    tubes = _tubes()
    result = cost_packaging({1: 25}, {1: tubes})
    assert result[1] == 25 * (tubes.purchase_price / tubes.purchase_volume)


def test_summarize_batch_cost_computes_grand_total() -> None:
    summary = summarize_batch_cost({1: 10.0}, {1: 5.0})
    assert summary["grand_total"] == 15.0


def test_minimum_restock_cost_when_moq_equals_purchase_volume() -> None:
    assert minimum_restock_cost(_tubes()) == 810


def test_minimum_restock_cost_scales_below_full_lot() -> None:
    half_lot_moq = Packaging(name="Jars", purchase_volume=1000, purchase_price=810, moq_for_price=500)
    assert minimum_restock_cost(half_lot_moq) == 405
