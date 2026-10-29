from fastlite import database

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


site_db = Database(SiteConfig().db_path)
