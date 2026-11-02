from datetime import datetime, timezone
from itertools import count, groupby
from logging import getLogger

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.db import site_db
from app.layout import site_layout
from app.models import Product

router = Fast.APIRouter()
logger = getLogger(__name__)

UNCATEGORIZED_LABEL = "Uncategorized"


def _formula_ingredient_names(formula_id: int) -> list[str]:
    """Public-safe view of a formula's recipe: ingredient names only, in
    insertion order. The exact proportions are the real trade secret
    (FormulaIngredient.percent) — same as a cosmetic product's printed
    ingredient list naming what's in it without disclosing the recipe's
    ratios — so this helper must never read or return `.percent`."""
    links = site_db.formula_ingredients(where="formula_id=?", where_args=[formula_id])
    names = []
    for link in links:
        try:
            names.append(site_db.ingredients.get(link.ingredient_id).name)
        except NotFoundError:
            continue
    return names


def _grouped_by_category(products: list[Product]) -> list[tuple[str, list[Product]]]:
    ordered = sorted(
        products, key=lambda product: (product.category or UNCATEGORIZED_LABEL, product.name)
    )
    return [
        (category, list(items))
        for category, items in groupby(
            ordered, key=lambda product: product.category or UNCATEGORIZED_LABEL
        )
    ]


def _product_row(index: int, product: Product) -> Fast.Li:
    return Fast.Li(
        Fast.A(
            Fast.Span(f"{index:03d}", cls="row-index"),
            Fast.Span(product.name, cls="row-title"),
            href=f"/products/{product.slug}",
            cls="row-link",
        )
    )


def _product_list(products: list[Product]) -> Fast.Div:
    row_number = count(1)
    return Fast.Div(
        *(
            Fast.Section(
                Fast.H2(category, cls="group-heading"),
                Fast.Ul(
                    *(_product_row(next(row_number), product) for product in items),
                    cls="row-list",
                ),
                cls="products-category-group",
            )
            for category, items in _grouped_by_category(products)
        ),
        cls="products-list",
    )


def _ingredient_table(names: list[str]) -> Fast.Table:
    """A specimen-style ingredient list matching the home page's lip-balm
    tiles — names only, deliberately no weight percentages (those are
    hers)."""
    return Fast.Table(
        Fast.Caption("Ingredients", cls="sr-only"),
        Fast.Thead(Fast.Tr(Fast.Th("Ingredient", scope="col"))),
        Fast.Tbody(*(Fast.Tr(Fast.Th(name, scope="row")) for name in names)),
        cls="ingredient-table",
    )


def _product_overlay(product: Product) -> Fast.Div:
    ingredient_names = (
        _formula_ingredient_names(product.formula_id) if product.formula_id else []
    )
    return Fast.Div(
        Fast.A(href="/products", cls="overlay-backdrop", aria_label="Close"),
        Fast.Div(
            Fast.A("Close", href="/products", cls="overlay-close", aria_label="Close"),
            Fast.H2(product.name, id="overlay-title"),
            Fast.Img(src=product.photo, alt="") if product.photo else None,
            Fast.P(product.description, cls="overlay-blurb"),
            Fast.Div(_ingredient_table(ingredient_names), cls="overlay-ingredients")
            if ingredient_names
            else None,
            cls="overlay-panel",
            role="dialog",
            aria_modal="true",
            aria_labelledby="overlay-title",
        ),
        cls="products-overlay",
        id="product-overlay",
    )


def _admin_product_row(product: Product) -> Fast.Li:
    return Fast.Li(
        Fast.Span(product.name, cls="row-title"),
        Fast.A("Edit", href=f"/admin/products/{product.slug}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/products/{product.slug}/delete",
        ),
        cls="admin-row",
    )


def _product_form(
    product: Product | None = None, *, action: str, show_slug_field: bool
) -> Fast.Form:
    product = product or Product()
    formulas = site_db.formulas(order_by="name")
    formula_options = [Fast.Option("— none —", value="")] + [
        Fast.Option(formula.name, value=str(formula.id)) for formula in formulas
    ]
    return Fast.Form(
        Fast.Label("Slug", Fast.Input(name="slug", value=product.slug, required=True))
        if show_slug_field
        else Fast.P(f"Slug: {product.slug}"),
        Fast.Label("Name", Fast.Input(name="name", value=product.name, required=True)),
        Fast.Label(
            "Description",
            Fast.Textarea(product.description, name="description", required=True),
        ),
        Fast.Label("Photo path", Fast.Input(name="photo", value=product.photo)),
        Fast.Label("Category", Fast.Input(name="category", value=product.category)),
        Fast.Label(
            "Formula link (ingredient names shown publicly, proportions never are)",
            Fast.Select(*formula_options, name="formula_id"),
        ),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


@router("/products")
def get():
    products = site_db.products(order_by="id")
    return site_layout(
        "Products",
        Fast.Div(
            Fast.H1("Products"),
            _product_list(products),
            cls="simple-page products-page",
        ),
    )


@router("/products/{slug}")
def get(slug: str):
    products = site_db.products(order_by="id")
    found = [product for product in products if product.slug == slug]
    if not found:
        raise Fast.HTTPException(status_code=404)
    product = found[0]
    return site_layout(
        product.name,
        Fast.Div(
            Fast.H1("Products"),
            _product_list(products),
            cls="simple-page products-page",
        ),
        _product_overlay(product),
    )


@router("/admin/products")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    products = site_db.products(order_by="id")
    return admin_layout(
        "Manage Products",
        Fast.H1("Manage Products"),
        Fast.Div(Fast.A("New Product", href="/admin/products/new"), cls="admin-action"),
        Fast.Ul(*(_admin_product_row(product) for product in products), cls="admin-list"),
    )


@router("/admin/products/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    return admin_layout(
        "New Product",
        Fast.H1("New Product"),
        _product_form(action="/admin/products/new", show_slug_field=True),
    )


@router("/admin/products/new")
def post(
    session,
    slug: str,
    name: str,
    description: str,
    photo: str = "",
    category: str = "",
    formula_id: str = "",
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    site_db.products.insert(
        Product(
            slug=slug,
            name=name,
            description=description,
            photo=photo,
            category=category,
            formula_id=int(formula_id) if formula_id else None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    logger.info("Created product %r", slug)
    return Fast.Redirect("/admin/products")


@router("/admin/products/{slug}/edit")
def get(slug: str, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.products(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    return admin_layout(
        "Edit Product",
        Fast.H1("Edit Product"),
        _product_form(found[0], action=f"/admin/products/{slug}/edit", show_slug_field=False),
    )


@router("/admin/products/{slug}/edit")
def post(
    slug: str,
    session,
    name: str,
    description: str,
    photo: str = "",
    category: str = "",
    formula_id: str = "",
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.products(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    site_db.products.update(
        {
            "id": found[0].id,
            "name": name,
            "description": description,
            "photo": photo,
            "category": category,
            "formula_id": int(formula_id) if formula_id else None,
        }
    )
    logger.info("Updated product %r", slug)
    return Fast.Redirect("/admin/products")


@router("/admin/products/{slug}/delete")
def post(slug: str, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.products(where="slug=?", where_args=[slug])
    if found:
        site_db.products.delete(found[0].id)
        logger.warning("Deleted product %r", slug)
    return Fast.Redirect("/admin/products")
