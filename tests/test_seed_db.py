from starlette.testclient import TestClient

from app.db import Database
from scripts.seed_db import seed


def test_seed_inserts_at_least_one_ingredient(client: TestClient, db: Database) -> None:
    seed(db)
    assert len(db.ingredients()) > 0


def test_seed_inserts_at_least_one_packaging_row(client: TestClient, db: Database) -> None:
    seed(db)
    assert len(db.packaging()) > 0


def test_seed_inserts_at_least_one_post(client: TestClient, db: Database) -> None:
    seed(db)
    assert len(db.posts()) > 0


def test_seed_inserts_every_formulas_ingredient_links_summing_to_100_percent(
    client: TestClient, db: Database
) -> None:
    seed(db)
    for formula in db.formulas():
        links = db.formula_ingredients(where="formula_id=?", where_args=[formula.id])
        assert round(sum(link.percent for link in links), 2) == 100.0


def test_seed_inserts_at_least_ten_formulas(client: TestClient, db: Database) -> None:
    seed(db)
    assert len(db.formulas()) >= 10


def test_seed_spreads_products_across_at_least_three_categories(
    client: TestClient, db: Database
) -> None:
    seed(db)
    categories = {product.category for product in db.products() if product.category}
    assert len(categories) >= 3


def test_seed_links_most_products_to_a_formula(client: TestClient, db: Database) -> None:
    seed(db)
    linked = db.products(where="formula_id IS NOT NULL")
    assert len(linked) >= 10


def test_seed_also_inserts_a_product_with_no_formula_link(
    client: TestClient, db: Database
) -> None:
    seed(db)
    unlinked = db.products(where="formula_id IS NULL")
    assert len(unlinked) > 0


def test_seeded_products_are_named_as_clearly_synthetic(
    client: TestClient, db: Database
) -> None:
    seed(db)
    assert all("Synthetic" in product.name for product in db.products())


def test_seeded_content_never_reuses_the_real_public_lip_balm_name(
    client: TestClient, db: Database
) -> None:
    seed(db)
    product_and_formula_names = {product.name for product in db.products()} | {
        formula.name for formula in db.formulas()
    }
    assert "Lip Balm" not in product_and_formula_names


def test_seeding_twice_duplicates_rows(client: TestClient, db: Database) -> None:
    """Documents the script's known not-idempotent behavior rather than
    silently relying on it — re-seeding an already-seeded DB is a known
    footgun, not a supported workflow (see seed_db.py's module docstring)."""
    seed(db)
    first_count = len(db.ingredients())
    seed(db)
    assert len(db.ingredients()) == first_count * 2
