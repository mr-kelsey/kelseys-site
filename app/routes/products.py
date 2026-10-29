from datetime import datetime, timezone
from logging import getLogger

from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.db import site_db
from app.layout import site_layout
from app.models import Product

router = Fast.APIRouter()
logger = getLogger(__name__)


def _product_row(index: int, product: Product) -> Fast.Li:
    return Fast.Li(
        Fast.A(
            Fast.Span(f"{index:03d}", cls="row-index"),
            Fast.Span(product.name, cls="row-title"),
            href=f"/products/{product.slug}",
            cls="row-link",
        )
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
        Fast.Label(
            "Internal formula link (never shown publicly)",
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
        Fast.H1("Products"),
        Fast.Ul(
            *(_product_row(i, product) for i, product in enumerate(products, start=1)),
            cls="row-list",
        ),
    )


@router("/products/{slug}")
def get(slug: str):
    found = site_db.products(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    product = found[0]
    return site_layout(
        product.name,
        Fast.A("Products", href="/products", cls="back-link"),
        Fast.H1(product.name),
        Fast.P(product.description),
        Fast.Img(src=product.photo) if product.photo else None,
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
