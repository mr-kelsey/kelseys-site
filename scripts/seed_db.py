"""Bootstraps a brand-new, empty data/app.db with real content.

TODO: no real Ingredient/Packaging/Formula/Product/Post content exists
yet — the old CLI's CSV data was scratch data, not real, and wasn't
migrated (see .claude/PLAN.md). Fill in REAL_* below once there's
actual content to seed. Not idempotent — re-running against an
already-seeded DB duplicates every row; use /admin for edits after the
initial seed."""

from app.db import site_db
from app.models import Formula, Ingredient, Packaging, Post, Product

REAL_INGREDIENTS: tuple[Ingredient, ...] = ()
REAL_PACKAGING: tuple[Packaging, ...] = ()
REAL_FORMULAS: tuple[Formula, ...] = ()
REAL_PRODUCTS: tuple[Product, ...] = ()
REAL_POSTS: tuple[Post, ...] = ()


def seed() -> None:
    for ingredient in REAL_INGREDIENTS:
        site_db.ingredients.insert(ingredient)
    for packaging in REAL_PACKAGING:
        site_db.packaging.insert(packaging)
    for formula in REAL_FORMULAS:
        site_db.formulas.insert(formula)
    for product in REAL_PRODUCTS:
        site_db.products.insert(product)
    for post in REAL_POSTS:
        site_db.posts.insert(post)


if __name__ == "__main__":
    seed()
