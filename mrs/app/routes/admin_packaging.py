from datetime import datetime, timezone
from logging import getLogger

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.db import site_db
from app.models import Packaging

router = Fast.APIRouter()
logger = getLogger(__name__)


def _admin_packaging_row(packaging: Packaging) -> Fast.Li:
    return Fast.Li(
        Fast.Span(packaging.name, cls="row-title"),
        Fast.A("Edit", href=f"/admin/packaging/{packaging.id}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/packaging/{packaging.id}/delete",
        ),
        cls="admin-row",
    )


def _packaging_form(packaging: Packaging | None = None, *, action: str) -> Fast.Form:
    packaging = packaging or Packaging()
    return Fast.Form(
        Fast.Label("Name", Fast.Input(name="name", value=packaging.name, required=True)),
        Fast.Label("Supplier", Fast.Input(name="supplier", value=packaging.supplier)),
        Fast.Label(
            "Purchase volume (pieces per lot)",
            Fast.Input(
                name="purchase_volume",
                type="number",
                value=packaging.purchase_volume,
                required=True,
            ),
        ),
        Fast.Label(
            "Purchase price (for that lot)",
            Fast.Input(
                name="purchase_price",
                type="number",
                step="any",
                value=packaging.purchase_price,
                required=True,
            ),
        ),
        Fast.Label(
            "Supplier's minimum order qty for that price",
            Fast.Input(
                name="moq_for_price",
                type="number",
                value=packaging.moq_for_price,
            ),
        ),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


@router("/admin/packaging")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    packaging_items = site_db.packaging(order_by="id")
    return admin_layout(
        "Manage Packaging",
        Fast.H1("Manage Packaging"),
        Fast.Div(Fast.A("New Packaging", href="/admin/packaging/new"), cls="admin-action"),
        Fast.Ul(*(_admin_packaging_row(item) for item in packaging_items), cls="admin-list"),
    )


@router("/admin/packaging/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    return admin_layout(
        "New Packaging",
        Fast.H1("New Packaging"),
        _packaging_form(action="/admin/packaging/new"),
    )


@router("/admin/packaging/new")
def post(
    session,
    name: str,
    purchase_volume: int,
    purchase_price: float,
    supplier: str = "",
    moq_for_price: int = 0,
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    site_db.packaging.insert(
        Packaging(
            name=name,
            supplier=supplier,
            purchase_volume=purchase_volume,
            purchase_price=purchase_price,
            moq_for_price=moq_for_price,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    logger.info("Created packaging %r", name)
    return Fast.Redirect("/admin/packaging")


@router("/admin/packaging/{packaging_id}/edit")
def get(packaging_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        packaging = site_db.packaging.get(packaging_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    return admin_layout(
        "Edit Packaging",
        Fast.H1("Edit Packaging"),
        _packaging_form(packaging, action=f"/admin/packaging/{packaging_id}/edit"),
    )


@router("/admin/packaging/{packaging_id}/edit")
def post(
    packaging_id: int,
    session,
    name: str,
    purchase_volume: int,
    purchase_price: float,
    supplier: str = "",
    moq_for_price: int = 0,
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.packaging.get(packaging_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    site_db.packaging.update(
        {
            "id": packaging_id,
            "name": name,
            "supplier": supplier,
            "purchase_volume": purchase_volume,
            "purchase_price": purchase_price,
            "moq_for_price": moq_for_price,
        }
    )
    logger.info("Updated packaging %r", name)
    return Fast.Redirect("/admin/packaging")


@router("/admin/packaging/{packaging_id}/delete")
def post(packaging_id: int, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        packaging = site_db.packaging.get(packaging_id)
    except NotFoundError:
        return Fast.Redirect("/admin/packaging")
    site_db.packaging.delete(packaging_id)
    logger.warning("Deleted packaging %r", packaging.name)
    return Fast.Redirect("/admin/packaging")
