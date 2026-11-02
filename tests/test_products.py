from starlette.testclient import TestClient

from app.db import Database
from app.models import Formula, FormulaIngredient, Ingredient, Product


def test_returns_200_for_products_index(client: TestClient) -> None:
    response = client.get("/products")
    assert response.status_code == 200


def test_products_index_lists_seeded_product_name(client: TestClient, db: Database) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    response = client.get("/products")
    assert "Lip Balm" in response.text


def test_products_index_groups_products_under_their_category_heading(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="a", name="A", description="d", category="Balms"))
    response = client.get("/products")
    assert "Balms" in response.text


def test_products_index_groups_uncategorized_products_under_fallback_heading(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="a", name="A", description="d"))
    response = client.get("/products")
    assert "Uncategorized" in response.text


def test_products_index_sorts_categories_alphabetically(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="z", name="Z", description="d", category="Zinc"))
    db.products.insert(Product(slug="a", name="A", description="d", category="Apples"))
    response = client.get("/products")
    assert response.text.index("Apples") < response.text.index("Zinc")


def test_products_index_does_not_render_an_overlay(client: TestClient, db: Database) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    response = client.get("/products")
    assert 'id="product-overlay"' not in response.text


def test_returns_200_for_known_product_slug(client: TestClient, db: Database) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    response = client.get("/products/lip-balm")
    assert response.status_code == 200


def test_product_detail_shows_description(client: TestClient, db: Database) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="Smooth and simple."))
    response = client.get("/products/lip-balm")
    assert "Smooth and simple." in response.text


def test_product_detail_renders_an_overlay(client: TestClient, db: Database) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    response = client.get("/products/lip-balm")
    assert 'id="product-overlay"' in response.text


def test_product_detail_still_lists_the_other_products_behind_the_overlay(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    db.products.insert(Product(slug="bright-lip-balm", name="Bright Lip Balm", description="d"))
    response = client.get("/products/lip-balm")
    assert "Bright Lip Balm" in response.text


def test_returns_404_for_unknown_product_slug(client: TestClient) -> None:
    response = client.get("/products/does-not-exist")
    assert response.status_code == 404


def test_product_linked_to_formula_shows_its_ingredient_names(
    client: TestClient, db: Database
) -> None:
    formula = db.formulas.insert(Formula(name="Lip Balm Secret Recipe", grams_per_unit=10.0))
    ingredient = db.ingredients.insert(Ingredient(name="Beeswax"))
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=37.5)
    )
    db.products.insert(
        Product(
            slug="lip-balm",
            name="Lip Balm",
            description="Smooth and simple.",
            formula_id=formula.id,
        )
    )
    response = client.get("/products/lip-balm")
    assert "Beeswax" in response.text


def test_product_linked_to_formula_never_exposes_formula_ingredient_percentages(
    client: TestClient, db: Database
) -> None:
    formula = db.formulas.insert(Formula(name="Lip Balm Secret Recipe", grams_per_unit=10.0))
    ingredient = db.ingredients.insert(Ingredient(name="Beeswax"))
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=37.5)
    )
    db.products.insert(
        Product(slug="lip-balm", name="Lip Balm", description="d", formula_id=formula.id)
    )
    response = client.get("/products/lip-balm")
    assert "37.5" not in response.text


def test_product_with_no_linked_formula_shows_no_ingredients_block(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    response = client.get("/products/lip-balm")
    assert "Ingredients" not in response.text
