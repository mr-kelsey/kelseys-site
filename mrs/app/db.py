from fastlite import NotFoundError, database

from app.config import SiteConfig
from app.models import (
    ContactMessage,
    Formula,
    FormulaIngredient,
    Ingredient,
    Packaging,
    Post,
    Product,
)


class Database:
    """Opens a fastlite connection at `db_path` and bootstraps the site's tables."""

    def __init__(self, db_path: str) -> None:
        self.connection = database(db_path)
        self.ingredients = self.connection.create(
            Ingredient, name="ingredients", pk="id", transform=True
        )
        self.packaging = self.connection.create(
            Packaging, name="packaging", pk="id", transform=True
        )
        self.formulas = self.connection.create(
            Formula, name="formulas", pk="id", transform=True
        )
        self.formula_ingredients = self.connection.create(
            FormulaIngredient, name="formula_ingredients", pk="id", transform=True
        )
        self.products = self.connection.create(
            Product, name="products", pk="id", transform=True
        )
        self.posts = self.connection.create(Post, name="posts", pk="id", transform=True)
        self.contact_messages = self.connection.create(
            ContactMessage, name="contact_messages", pk="id", transform=True
        )

    def public_ingredient_names(self, formula_id: int) -> list[str]:
        """Public-safe view of a formula's recipe: ingredient names only,
        in insertion order. The exact proportions are the real trade
        secret (FormulaIngredient.percent) — same as a cosmetic product's
        printed ingredient list naming what's in it without disclosing
        the recipe's ratios — so this must never read or return `.percent`."""
        links = self.formula_ingredients(where="formula_id=?", where_args=[formula_id])
        names = []
        for link in links:
            try:
                names.append(self.ingredients.get(link.ingredient_id).name)
            except NotFoundError:
                continue
        return names


site_db = Database(SiteConfig().db_path)
