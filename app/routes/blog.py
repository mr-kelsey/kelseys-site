from datetime import datetime, timezone
from logging import getLogger

from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.db import site_db
from app.layout import site_layout
from app.models import Post

router = Fast.APIRouter()
logger = getLogger(__name__)


def _post_row(index: int, post) -> Fast.Li:
    return Fast.Li(
        Fast.A(
            Fast.Span(f"{index:03d}", cls="row-index"),
            Fast.Span(post.title, cls="row-title"),
            href=f"/blog/{post.slug}",
            cls="row-link",
        )
    )


def _admin_post_row(post) -> Fast.Li:
    return Fast.Li(
        Fast.Span(post.title, cls="row-title"),
        Fast.A("Edit", href=f"/admin/blog/{post.slug}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/blog/{post.slug}/delete",
        ),
        cls="admin-row",
    )


def _post_form(post: Post | None = None, *, action: str, show_slug_field: bool) -> Fast.Form:
    post = post or Post()
    return Fast.Form(
        Fast.Label("Slug", Fast.Input(name="slug", value=post.slug, required=True))
        if show_slug_field
        else Fast.P(f"Slug: {post.slug}"),
        Fast.Label("Title", Fast.Input(name="title", value=post.title, required=True)),
        Fast.Label("Body", Fast.Textarea(post.body, name="body", required=True)),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
    )


@router("/blog")
def get():
    posts = site_db.posts(order_by="id")
    return site_layout(
        "Blog",
        Fast.H1("Blog"),
        Fast.Ul(
            *(_post_row(i, post) for i, post in enumerate(posts, start=1)),
            cls="row-list",
        ),
    )


@router("/admin/blog")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    posts = site_db.posts(order_by="id")
    return admin_layout(
        "Manage Blog",
        Fast.H1("Manage Blog"),
        Fast.Div(Fast.A("New Post", href="/admin/blog/new"), cls="admin-action"),
        Fast.Ul(*(_admin_post_row(post) for post in posts), cls="admin-list"),
    )


@router("/admin/blog/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    return admin_layout(
        "New Post",
        Fast.H1("New Post"),
        _post_form(action="/admin/blog/new", show_slug_field=True),
    )


@router("/admin/blog/new")
def post(session, slug: str, title: str, body: str):
    if (redirect := require_admin(session)) is not None:
        return redirect
    site_db.posts.insert(
        Post(
            slug=slug,
            title=title,
            body=body,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    logger.info("Created post %r", slug)
    return Fast.Redirect("/admin/blog")


@router("/admin/blog/{slug}/edit")
def get(slug: str, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.posts(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    return admin_layout(
        "Edit Post",
        Fast.H1("Edit Post"),
        _post_form(found[0], action=f"/admin/blog/{slug}/edit", show_slug_field=False),
    )


@router("/admin/blog/{slug}/edit")
def post(slug: str, session, title: str, body: str):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.posts(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    site_db.posts.update({"id": found[0].id, "title": title, "body": body})
    logger.info("Updated post %r", slug)
    return Fast.Redirect("/admin/blog")


@router("/admin/blog/{slug}/delete")
def post(slug: str, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.posts(where="slug=?", where_args=[slug])
    if found:
        site_db.posts.delete(found[0].id)
        logger.warning("Deleted post %r", slug)
    return Fast.Redirect("/admin/blog")


@router("/blog/{slug}")
def get(slug: str):
    found = site_db.posts(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    post = found[0]
    return site_layout(
        post.title,
        Fast.A("Blog", href="/blog", cls="back-link"),
        Fast.H1(post.title),
        *(Fast.P(paragraph) for paragraph in post.body.split("\n\n") if paragraph),
    )
