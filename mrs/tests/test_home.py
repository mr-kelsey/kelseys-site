from starlette.testclient import TestClient

from app.db import Database
from app.models import Formula, FormulaIngredient, Ingredient, Product


def test_returns_200_for_home_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_home_page_includes_nav_link_to_products(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/products"' in response.text


def test_home_page_includes_nav_link_to_about(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/#about"' in response.text


def test_home_page_includes_nav_link_to_contact(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/contact"' in response.text


def test_home_page_includes_fixed_reveal_layer(client: TestClient) -> None:
    response = client.get("/")
    assert 'class="reveal-stage"' in response.text


def test_home_page_never_shows_a_linked_formulas_ingredient_percentage(
    client: TestClient, db: Database
) -> None:
    formula = db.formulas.insert(Formula(name="Secret Recipe", grams_per_unit=10.0))
    ingredient = db.ingredients.insert(Ingredient(name="Beeswax"))
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=37.5)
    )
    db.products.insert(
        Product(slug="sample", name="Sample", description="d", formula_id=formula.id)
    )
    response = client.get("/")
    assert "37.5" not in response.text


def test_home_page_pitches_private_label_to_businesses(client: TestClient) -> None:
    response = client.get("/")
    assert "Private label is a revenue line" in response.text


def test_home_page_names_a_real_partner_company(client: TestClient) -> None:
    response = client.get("/")
    assert "Drop Dead Gorgeous" in response.text


def test_home_page_marks_credentials_as_placeholder(client: TestClient) -> None:
    response = client.get("/")
    assert "to be added" in response.text


def test_home_page_shows_a_product_pulled_from_the_db(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="sample", name="Sample Product Item", description="d"))
    response = client.get("/")
    assert "Sample Product Item" in response.text


def test_home_page_product_tile_links_straight_to_the_product_page(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="sample", name="Sample Product Item", description="d"))
    response = client.get("/")
    assert 'href="/products/sample"' in response.text


def test_home_page_featured_tile_shows_ingredient_table_when_formula_linked(
    client: TestClient, db: Database
) -> None:
    formula = db.formulas.insert(Formula(name="Recipe", grams_per_unit=10.0))
    ingredient = db.ingredients.insert(Ingredient(name="Beeswax"))
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=50.0)
    )
    db.products.insert(
        Product(slug="sample", name="Sample", description="d", formula_id=formula.id)
    )
    response = client.get("/")
    assert 'class="ingredient-table"' in response.text


def test_home_page_featured_tile_shows_the_ingredient_names(
    client: TestClient, db: Database
) -> None:
    formula = db.formulas.insert(Formula(name="Recipe", grams_per_unit=10.0))
    ingredient = db.ingredients.insert(Ingredient(name="Beeswax"))
    db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=50.0)
    )
    db.products.insert(
        Product(slug="sample", name="Sample", description="d", formula_id=formula.id)
    )
    response = client.get("/")
    assert "Beeswax" in response.text


def test_home_page_featured_tile_falls_back_to_blurb_when_not_formula_linked(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="sample", name="Sample", description="A short blurb."))
    response = client.get("/")
    assert "A short blurb." in response.text


def test_home_page_featured_tile_omits_ingredient_table_when_not_formula_linked(
    client: TestClient, db: Database
) -> None:
    db.products.insert(Product(slug="sample", name="Sample", description="A short blurb."))
    response = client.get("/")
    assert 'class="ingredient-table"' not in response.text


def test_home_page_caps_the_featured_sample_at_two_products(
    client: TestClient, db: Database
) -> None:
    for i in range(10):
        db.products.insert(Product(slug=f"sample-{i}", name=f"Sample {i}", description="d"))
    response = client.get("/")
    featured_html, _, _ = response.text.partition('id="workbench-products"')
    assert featured_html.count('class="tile tile--link"') == 2


def test_home_page_caps_the_workbench_sample_at_six_products(
    client: TestClient, db: Database
) -> None:
    for i in range(10):
        db.products.insert(Product(slug=f"sample-{i}", name=f"Sample {i}", description="d"))
    response = client.get("/")
    _, _, workbench_html = response.text.partition('id="workbench-products"')
    assert workbench_html.count('class="tile tile--link"') == 6


def test_home_page_never_repeats_a_product_across_both_rows(
    client: TestClient, db: Database
) -> None:
    for i in range(10):
        db.products.insert(Product(slug=f"sample-{i}", name=f"Sample {i}", description="d"))
    response = client.get("/")
    featured_html, _, workbench_html = response.text.partition('id="workbench-products"')
    assert not any(
        f'href="/products/sample-{i}"' in featured_html
        and f'href="/products/sample-{i}"' in workbench_html
        for i in range(10)
    )


def test_home_page_omits_featured_heading_when_no_products_exist(
    client: TestClient,
) -> None:
    response = client.get("/")
    assert "Featured now" not in response.text


def test_home_page_omits_workbench_heading_when_no_products_exist(
    client: TestClient,
) -> None:
    response = client.get("/")
    assert "Also from the workbench" not in response.text
