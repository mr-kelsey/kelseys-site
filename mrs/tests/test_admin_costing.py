from starlette.testclient import TestClient

from app.db import Database
from app.models import Formula, FormulaIngredient, Ingredient, Packaging


def _insert_formula_with_one_ingredient(db: Database) -> tuple[int, int]:
    formula = db.formulas.insert(Formula(name="Lip Balm", grams_per_unit=10.0))
    ingredient = db.ingredients.insert(
        Ingredient(name="White Beeswax", purchase_volume=16, total_grams=453.59, purchase_price=16)
    )
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=100.0)
    )
    return formula.id, ingredient.id


def _insert_packaging(db: Database) -> int:
    inserted = db.packaging.insert(
        Packaging(name="Lip Balm Tubes", purchase_volume=1000, purchase_price=810, moq_for_price=1000)
    )
    return inserted.id


def test_get_admin_formula_cost_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/formulas/1/cost", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_formula_cost_returns_200_for_existing_formula(
    admin_client: TestClient, db: Database
) -> None:
    formula_id, _ = _insert_formula_with_one_ingredient(db)
    response = admin_client.get(f"/admin/formulas/{formula_id}/cost")
    assert response.status_code == 200


def test_get_admin_formula_cost_returns_404_for_unknown_formula(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/formulas/999/cost")
    assert response.status_code == 404


def test_post_admin_formula_cost_with_unit_count_shows_grand_total(
    admin_client: TestClient, db: Database
) -> None:
    formula_id, _ = _insert_formula_with_one_ingredient(db)
    response = admin_client.post(
        f"/admin/formulas/{formula_id}/cost", data={"unit_count": "2"}
    )
    expected_cost = round(2 * 10.0 * (16 / 453.59), 2)
    assert f"{expected_cost}" in response.text


def test_post_admin_formula_cost_with_target_grams_shows_grand_total(
    admin_client: TestClient, db: Database
) -> None:
    formula_id, _ = _insert_formula_with_one_ingredient(db)
    response = admin_client.post(
        f"/admin/formulas/{formula_id}/cost", data={"target_grams": "20"}
    )
    expected_cost = round(20 * (16 / 453.59), 2)
    assert f"{expected_cost}" in response.text


def test_post_admin_formula_cost_with_both_unit_count_and_target_grams_shows_error(
    admin_client: TestClient, db: Database
) -> None:
    formula_id, _ = _insert_formula_with_one_ingredient(db)
    response = admin_client.post(
        f"/admin/formulas/{formula_id}/cost",
        data={"unit_count": "2", "target_grams": "20"},
    )
    assert "exactly one" in response.text.lower()


def test_post_admin_formula_cost_shows_packaging_minimum_restock_cost(
    admin_client: TestClient, db: Database
) -> None:
    formula_id, _ = _insert_formula_with_one_ingredient(db)
    packaging_id = _insert_packaging(db)
    response = admin_client.post(
        f"/admin/formulas/{formula_id}/cost",
        data={
            "unit_count": "2",
            "packaging_id": [str(packaging_id)],
            "packaging_quantity": ["2"],
        },
    )
    assert "810" in response.text


def test_post_admin_formula_cost_returns_404_for_unknown_formula(
    admin_client: TestClient,
) -> None:
    response = admin_client.post("/admin/formulas/999/cost", data={"unit_count": "2"})
    assert response.status_code == 404
