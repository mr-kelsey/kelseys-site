from starlette.testclient import TestClient

from app.db import Database
from app.models import Formula, FormulaIngredient, Ingredient

VALID_FORMULA_SHELL_FORM = {"name": "Lip Balm", "grams_per_unit": "10.0"}


def _insert_formula(db: Database) -> int:
    inserted = db.formulas.insert(Formula(name="Lip Balm", grams_per_unit=10.0))
    return inserted.id


def _insert_ingredient(db: Database, name: str = "White Beeswax") -> int:
    inserted = db.ingredients.insert(
        Ingredient(name=name, purchase_volume=16, total_grams=453.59, purchase_price=12)
    )
    return inserted.id


def test_get_admin_formulas_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/formulas", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_formulas_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/formulas")
    assert response.status_code == 200


def test_get_admin_formulas_new_returns_200(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/formulas/new")
    assert response.status_code == 200


def test_post_admin_formulas_new_creates_formula(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/formulas/new", data=VALID_FORMULA_SHELL_FORM)
    assert db.formulas.count == 1


def test_post_admin_formulas_new_redirects_to_its_edit_page(
    admin_client: TestClient, db: Database
) -> None:
    response = admin_client.post(
        "/admin/formulas/new", data=VALID_FORMULA_SHELL_FORM, follow_redirects=False
    )
    [formula] = db.formulas(order_by="id")
    assert response.headers["location"] == f"/admin/formulas/{formula.id}/edit"


def test_post_admin_formulas_new_without_auth_does_not_create(
    client: TestClient, db: Database
) -> None:
    client.post("/admin/formulas/new", data=VALID_FORMULA_SHELL_FORM)
    assert db.formulas.count == 0


def test_get_admin_formula_detail_returns_200_for_existing_id(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    response = admin_client.get(f"/admin/formulas/{formula_id}")
    assert response.status_code == 200


def test_get_admin_formula_detail_shows_ingredient_percent(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    ingredient_id = _insert_ingredient(db)
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula_id, ingredient_id=ingredient_id, percent=100.0)
    )
    response = admin_client.get(f"/admin/formulas/{formula_id}")
    assert "White Beeswax" in response.text


def test_get_admin_formula_detail_returns_404_for_unknown_id(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/formulas/999")
    assert response.status_code == 404


def test_get_admin_formulas_edit_returns_200_for_existing_id(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    response = admin_client.get(f"/admin/formulas/{formula_id}/edit")
    assert response.status_code == 200


def test_get_admin_formulas_edit_returns_404_for_unknown_id(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin/formulas/999/edit")
    assert response.status_code == 404


def test_post_admin_formulas_edit_updates_name(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    admin_client.post(
        f"/admin/formulas/{formula_id}/edit",
        data={"name": "Bright Lip Balm", "grams_per_unit": "10.0"},
    )
    assert db.formulas.get(formula_id).name == "Bright Lip Balm"


def test_post_admin_formulas_edit_with_blank_recipe_rows_keeps_existing_recipe(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    ingredient_id = _insert_ingredient(db)
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula_id, ingredient_id=ingredient_id, percent=100.0)
    )
    admin_client.post(
        f"/admin/formulas/{formula_id}/edit",
        data={"name": "Lip Balm", "grams_per_unit": "10.0"},
    )
    links = db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    assert len(links) == 1


def test_post_admin_formulas_edit_with_recipe_recomputes_single_ingredient_to_100_percent(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    ingredient_id = _insert_ingredient(db)
    admin_client.post(
        f"/admin/formulas/{formula_id}/edit",
        data={
            "name": "Lip Balm",
            "grams_per_unit": "10.0",
            "ingredient_id": [str(ingredient_id)],
            "quantity": ["3"],
        },
    )
    [link] = db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    assert link.percent == 100.0


def test_post_admin_formulas_edit_with_new_recipe_replaces_old_links(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    old_ingredient_id = _insert_ingredient(db, "Old Ingredient")
    new_ingredient_id = _insert_ingredient(db, "New Ingredient")
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula_id, ingredient_id=old_ingredient_id, percent=100.0)
    )
    admin_client.post(
        f"/admin/formulas/{formula_id}/edit",
        data={
            "name": "Lip Balm",
            "grams_per_unit": "10.0",
            "ingredient_id": [str(new_ingredient_id)],
            "quantity": ["3"],
        },
    )
    links = db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    assert [link.ingredient_id for link in links] == [new_ingredient_id]


def test_post_admin_formulas_edit_redirects_to_detail_page(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    response = admin_client.post(
        f"/admin/formulas/{formula_id}/edit",
        data={"name": "Lip Balm", "grams_per_unit": "10.0"},
        follow_redirects=False,
    )
    assert response.headers["location"] == f"/admin/formulas/{formula_id}"


def test_post_admin_formulas_delete_removes_formula(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    admin_client.post(f"/admin/formulas/{formula_id}/delete")
    assert db.formulas.count == 0


def test_post_admin_formulas_delete_removes_its_formula_ingredients(
    admin_client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    ingredient_id = _insert_ingredient(db)
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula_id, ingredient_id=ingredient_id, percent=100.0)
    )
    admin_client.post(f"/admin/formulas/{formula_id}/delete")
    links = db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    assert links == []


def test_post_admin_formulas_delete_without_auth_does_not_remove(
    client: TestClient, db: Database
) -> None:
    formula_id = _insert_formula(db)
    client.post(f"/admin/formulas/{formula_id}/delete")
    assert db.formulas.count == 1
