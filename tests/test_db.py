from collections.abc import Iterator
from os import close as close_fd
from pathlib import Path
from tempfile import mkstemp

from fastlite import NotFoundError
from pytest import fixture, raises

from app.db import Database
from app.models import (
    ContactMessage,
    Formula,
    FormulaIngredient,
    Ingredient,
    Packaging,
    Post,
    Product,
)


@fixture()
def db() -> Iterator[Database]:
    file_descriptor, db_path = mkstemp(suffix=".db")
    close_fd(file_descriptor)
    db_path = Path(db_path)
    try:
        yield Database(str(db_path))
    finally:
        db_path.unlink()


def test_creates_ingredients_table(db: Database) -> None:
    assert "ingredients" in db.connection.table_names()


def test_creates_packaging_table(db: Database) -> None:
    assert "packaging" in db.connection.table_names()


def test_creates_formulas_table(db: Database) -> None:
    assert "formulas" in db.connection.table_names()


def test_creates_formula_ingredients_table(db: Database) -> None:
    assert "formula_ingredients" in db.connection.table_names()


def test_creates_products_table(db: Database) -> None:
    assert "products" in db.connection.table_names()


def test_creates_posts_table(db: Database) -> None:
    assert "posts" in db.connection.table_names()


def test_creates_contact_messages_table(db: Database) -> None:
    assert "contact_messages" in db.connection.table_names()


def test_inserted_ingredient_is_retrievable_by_id(db: Database) -> None:
    inserted = db.ingredients.insert(
        Ingredient(
            name="White Beeswax",
            vendor="Mary Tyler Naturals",
            purchase_volume=16,
            volume_unit="oz",
            total_grams=453.59,
            purchase_price=12,
        )
    )
    assert db.ingredients.get(inserted.id).name == "White Beeswax"


def test_inserted_packaging_is_retrievable_by_id(db: Database) -> None:
    inserted = db.packaging.insert(
        Packaging(
            name="Lip Balm Tubes",
            supplier="China",
            purchase_volume=1000,
            purchase_price=810,
            moq_for_price=1000,
        )
    )
    assert db.packaging.get(inserted.id).supplier == "China"


def test_inserted_formula_is_retrievable_by_id(db: Database) -> None:
    inserted = db.formulas.insert(Formula(name="Lip Balm", grams_per_unit=10.7112))
    assert db.formulas.get(inserted.id).name == "Lip Balm"


def test_inserted_formula_ingredient_links_formula_and_ingredient(db: Database) -> None:
    formula = db.formulas.insert(Formula(name="Lip Balm", grams_per_unit=10.7112))
    ingredient = db.ingredients.insert(Ingredient(name="White Beeswax"))
    inserted = db.formula_ingredients.insert(
        FormulaIngredient(formula_id=formula.id, ingredient_id=ingredient.id, percent=21.17)
    )
    found = db.formula_ingredients.get(inserted.id)
    assert (found.formula_id, found.ingredient_id) == (formula.id, ingredient.id)


def test_inserted_product_is_retrievable_by_slug(db: Database) -> None:
    db.products.insert(Product(slug="lip-balm", name="Lip Balm", description="d"))
    found = db.products(where="slug=?", where_args=["lip-balm"])
    assert found[0].name == "Lip Balm"


def test_missing_product_slug_returns_no_rows(db: Database) -> None:
    found = db.products(where="slug=?", where_args=["does-not-exist"])
    assert found == []


def test_inserted_post_is_retrievable_by_slug(db: Database) -> None:
    db.posts.insert(Post(slug="first-post", title="First Post", body="body"))
    found = db.posts(where="slug=?", where_args=["first-post"])
    assert found[0].title == "First Post"


def test_inserted_contact_message_is_persisted(db: Database) -> None:
    db.contact_messages.insert(
        ContactMessage(name="Alex", email="alex@example.com", message="Hi")
    )
    assert db.contact_messages.count == 1


def test_ingredient_get_raises_for_unknown_id(db: Database) -> None:
    with raises(NotFoundError):
        db.ingredients.get(999)
