"""Bootstraps a brand-new, empty data/app.db with synthetic dev/test content.

See .claude/NEXT_STEPS.md: the stakeholder won't disclose formulas
beyond the two already public (Lip Balm, Bright Lip Balm), so the
content below is clearly-labeled synthetic placeholder data for local
dev and automated tests only — never anything resembling her real
recipes, and the categories here are made up for testing the grouping
UI, not her real taxonomy. Her actual data goes in through /admin
directly, not through this script.

Not idempotent — re-running against an already-seeded DB duplicates
every row; use /admin for edits after the initial seed."""

from dataclasses import dataclass
from datetime import datetime, timezone
from re import sub as re_sub

from app.db import Database, site_db
from app.models import Formula, FormulaIngredient, Ingredient, Packaging, Post, Product

SYNTHETIC_INGREDIENTS: tuple[Ingredient, ...] = (
    Ingredient(
        name="Synthetic Carrier Oil A",
        vendor="Dev Fixture Co",
        purchase_volume=16.0,
        volume_unit="oz",
        total_grams=453.0,
        purchase_price=12.50,
    ),
    Ingredient(
        name="Synthetic Carrier Oil B",
        vendor="Dev Fixture Co",
        purchase_volume=16.0,
        volume_unit="oz",
        total_grams=453.0,
        purchase_price=14.00,
    ),
    Ingredient(
        name="Synthetic Butter Base A",
        vendor="Dev Fixture Co",
        purchase_volume=1.0,
        volume_unit="lb",
        total_grams=453.0,
        purchase_price=9.00,
    ),
    Ingredient(
        name="Synthetic Butter Base B",
        vendor="Dev Fixture Co",
        purchase_volume=1.0,
        volume_unit="lb",
        total_grams=453.0,
        purchase_price=10.50,
    ),
    Ingredient(
        name="Synthetic Wax Base",
        vendor="Dev Fixture Co",
        purchase_volume=1.0,
        volume_unit="lb",
        total_grams=453.0,
        purchase_price=11.00,
    ),
    Ingredient(
        name="Synthetic Essential Oil Blend A",
        vendor="Dev Fixture Co",
        purchase_volume=10.0,
        volume_unit="ml",
        total_grams=9.0,
        purchase_price=15.00,
    ),
    Ingredient(
        name="Synthetic Essential Oil Blend B",
        vendor="Dev Fixture Co",
        purchase_volume=10.0,
        volume_unit="ml",
        total_grams=9.0,
        purchase_price=16.50,
    ),
    Ingredient(
        name="Synthetic Essential Oil Blend C",
        vendor="Dev Fixture Co",
        purchase_volume=10.0,
        volume_unit="ml",
        total_grams=9.0,
        purchase_price=18.00,
    ),
    Ingredient(
        name="Synthetic Active Extract",
        vendor="Dev Fixture Co",
        purchase_volume=4.0,
        volume_unit="oz",
        total_grams=113.0,
        purchase_price=22.00,
    ),
    Ingredient(
        name="Synthetic Humectant",
        vendor="Dev Fixture Co",
        purchase_volume=8.0,
        volume_unit="oz",
        total_grams=227.0,
        purchase_price=13.00,
    ),
)

SYNTHETIC_PACKAGING: tuple[Packaging, ...] = (
    Packaging(
        name="Synthetic 2oz Tin",
        supplier="Dev Fixture Co",
        purchase_volume=100,
        purchase_price=38.00,
        moq_for_price=100,
    ),
)


@dataclass
class SyntheticFormulaSpec:
    """One made-up formula: its name, display category, expected unit
    yield, and recipe as (ingredient index into SYNTHETIC_INGREDIENTS,
    weight percent) pairs that must sum to 100."""

    name: str
    category: str
    grams_per_unit: float
    recipe: tuple[tuple[int, float], ...]


SYNTHETIC_FORMULA_SPECS: tuple[SyntheticFormulaSpec, ...] = (
    # ---- Synthetic Balms ----
    SyntheticFormulaSpec(
        "Synthetic Everyday Balm",
        "Synthetic Balms",
        15.0,
        ((4, 40.0), (0, 35.0), (2, 15.0), (5, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Cooling Balm",
        "Synthetic Balms",
        15.0,
        ((4, 35.0), (1, 30.0), (3, 20.0), (6, 10.0), (8, 5.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Repair Balm",
        "Synthetic Balms",
        15.0,
        ((2, 45.0), (0, 30.0), (4, 15.0), (7, 10.0)),
    ),
    # ---- Synthetic Facial Care ----
    SyntheticFormulaSpec(
        "Synthetic Clarifying Serum",
        "Synthetic Facial Care",
        30.0,
        ((1, 50.0), (8, 25.0), (9, 15.0), (5, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Nourishing Night Cream",
        "Synthetic Facial Care",
        50.0,
        ((3, 40.0), (0, 30.0), (9, 20.0), (6, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Gentle Toner Concentrate",
        "Synthetic Facial Care",
        100.0,
        ((9, 60.0), (8, 25.0), (7, 15.0)),
    ),
    # ---- Synthetic Body Care ----
    SyntheticFormulaSpec(
        "Synthetic Whipped Body Butter",
        "Synthetic Body Care",
        100.0,
        ((2, 50.0), (3, 25.0), (0, 15.0), (5, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Massage Oil Blend",
        "Synthetic Body Care",
        50.0,
        ((0, 55.0), (1, 35.0), (6, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Exfoliating Scrub Base",
        "Synthetic Body Care",
        100.0,
        ((1, 45.0), (2, 30.0), (9, 15.0), (7, 10.0)),
    ),
    # ---- Synthetic Aromatherapy ----
    SyntheticFormulaSpec(
        "Synthetic Calming Roller Blend",
        "Synthetic Aromatherapy",
        10.0,
        ((0, 70.0), (5, 20.0), (6, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Energizing Roller Blend",
        "Synthetic Aromatherapy",
        10.0,
        ((1, 65.0), (7, 25.0), (8, 10.0)),
    ),
    SyntheticFormulaSpec(
        "Synthetic Diffuser Blend Concentrate",
        "Synthetic Aromatherapy",
        15.0,
        ((5, 40.0), (6, 35.0), (7, 25.0)),
    ),
)

SYNTHETIC_POSTS: tuple[Post, ...] = (
    Post(
        slug="synthetic-dev-post",
        title="Synthetic Dev Post",
        body="Placeholder blog content for local dev/testing.",
    ),
)

_PRODUCT_DESCRIPTION = (
    "Placeholder product for local dev/testing — not a real "
    "Kaleidoscopic Creations product."
)


def _slugify(name: str) -> str:
    return re_sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def seed(db: Database = site_db) -> None:
    now = datetime.now(timezone.utc).isoformat()

    inserted_ingredients = [
        db.ingredients.insert(
            Ingredient(
                name=ingredient.name,
                vendor=ingredient.vendor,
                purchase_volume=ingredient.purchase_volume,
                volume_unit=ingredient.volume_unit,
                total_grams=ingredient.total_grams,
                purchase_price=ingredient.purchase_price,
                created_at=now,
            )
        )
        for ingredient in SYNTHETIC_INGREDIENTS
    ]

    for packaging in SYNTHETIC_PACKAGING:
        db.packaging.insert(
            Packaging(
                name=packaging.name,
                supplier=packaging.supplier,
                purchase_volume=packaging.purchase_volume,
                purchase_price=packaging.purchase_price,
                moq_for_price=packaging.moq_for_price,
                created_at=now,
            )
        )

    for spec in SYNTHETIC_FORMULA_SPECS:
        formula = db.formulas.insert(
            Formula(
                name=spec.name,
                grams_per_unit=spec.grams_per_unit,
                notes="Synthetic dev/test fixture — not a real recipe.",
                created_at=now,
            )
        )
        for ingredient_index, percent in spec.recipe:
            db.formula_ingredients.insert(
                FormulaIngredient(
                    formula_id=formula.id,
                    ingredient_id=inserted_ingredients[ingredient_index].id,
                    percent=percent,
                )
            )
        db.products.insert(
            Product(
                slug=_slugify(spec.name),
                name=f"{spec.name} (Dev Placeholder)",
                description=_PRODUCT_DESCRIPTION,
                formula_id=formula.id,
                category=spec.category,
                created_at=now,
            )
        )

    db.products.insert(
        Product(
            slug="synthetic-no-formula-sample",
            name="Synthetic No-Formula Sample (Dev Placeholder)",
            description=(
                "Placeholder product with no linked formula, for local "
                "dev/testing — not a real Kaleidoscopic Creations product."
            ),
            created_at=now,
        )
    )

    for post in SYNTHETIC_POSTS:
        db.posts.insert(
            Post(
                slug=post.slug,
                title=post.title,
                body=post.body,
                created_at=now,
            )
        )


if __name__ == "__main__":
    seed()
