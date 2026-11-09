from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

from fasthtml import common as Fast
from starlette.responses import FileResponse

from app.auth import admin_layout, require_admin
from app.config import SiteConfig
from app.db import site_db
from app.layout import site_layout
from app.models import Project
from app.text import normalize_line_endings

router = Fast.APIRouter()
logger = getLogger(__name__)

REPORT_PDF_CONTENT_TYPE = "application/pdf"


def _report_pdf_file_path(slug: str) -> Path:
    return Path(SiteConfig().reports_dir) / f"{slug}.pdf"


def _report_pdf_url(slug: str) -> str:
    return f"/reports/{slug}.pdf"


def _has_pdf_upload(upload: Fast.UploadFile | None) -> bool:
    return bool(upload and upload.filename)


def _looks_like_pdf(upload: Fast.UploadFile) -> bool:
    return upload.content_type == REPORT_PDF_CONTENT_TYPE or upload.filename.lower().endswith(
        ".pdf"
    )


def _save_report_pdf(slug: str, upload: Fast.UploadFile) -> str:
    """Persists an uploaded report PDF under the slug's own filename --
    never the browser-supplied filename -- so there's no path-traversal
    surface from user-controlled input. Stored under SiteConfig.reports_dir,
    which lives in the app-data Docker volume (same as the SQLite DB), not
    under static/ -- static/ is baked into the image at build time and
    wouldn't survive the next deploy."""
    destination = _report_pdf_file_path(slug)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(upload.file.read())
    return _report_pdf_url(slug)


def _project_row(index: int, project) -> Fast.Li:
    return Fast.Li(
        Fast.A(
            Fast.Span(f"{index:03d}", cls="row-index"),
            Fast.Span(project.title, cls="row-title"),
            Fast.Span(project.description, cls="row-detail"),
            href=f"/work/{project.slug}",
            cls="row-link",
        )
    )


def _admin_project_row(project) -> Fast.Li:
    return Fast.Li(
        Fast.Span(project.title, cls="row-title"),
        Fast.A("Edit", href=f"/admin/work/{project.slug}/edit"),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/work/{project.slug}/delete",
        ),
        cls="admin-row",
    )


def _project_form(project: Project | None = None, *, action: str, show_slug_field: bool) -> Fast.Form:
    project = project or Project()
    return Fast.Form(
        Fast.Label("Slug", Fast.Input(name="slug", value=project.slug, required=True))
        if show_slug_field
        else Fast.P(f"Slug: {project.slug}"),
        Fast.Label("Title", Fast.Input(name="title", value=project.title, required=True)),
        Fast.Label(
            "Description",
            Fast.Textarea(project.description, name="description", required=True),
        ),
        Fast.Label("Body", Fast.Textarea(project.body, name="body", required=True)),
        Fast.Label("URL", Fast.Input(name="url", value=project.url)),
        Fast.P(f"Current report PDF: {project.report_pdf}") if project.report_pdf else None,
        Fast.Label(
            "Report PDF (leave blank to keep current)" if project.report_pdf else "Report PDF",
            Fast.Input(name="report_pdf_upload", type="file", accept="application/pdf"),
        ),
        Fast.Button("Save", type="submit"),
        method="post",
        action=action,
        enctype="multipart/form-data",
    )


@router("/work")
def get():
    projects = site_db.projects(order_by="id")
    return site_layout(
        "Work",
        Fast.H1("Work"),
        Fast.Ul(
            *(_project_row(i, project) for i, project in enumerate(projects, start=1)),
            cls="row-list",
        ),
    )


@router("/admin/work")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    projects = site_db.projects(order_by="id")
    return admin_layout(
        "Manage Work",
        Fast.H1("Manage Work"),
        Fast.Div(Fast.A("New Project", href="/admin/work/new"), cls="admin-action"),
        Fast.Ul(*(_admin_project_row(project) for project in projects), cls="admin-list"),
    )


@router("/admin/work/new")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    return admin_layout(
        "New Project",
        Fast.H1("New Project"),
        _project_form(action="/admin/work/new", show_slug_field=True),
    )


@router("/admin/work/new")
def post(
    session,
    slug: str,
    title: str,
    description: str,
    body: str,
    url: str = "",
    report_pdf_upload: Fast.UploadFile | None = None,
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    report_pdf = ""
    if _has_pdf_upload(report_pdf_upload):
        if not _looks_like_pdf(report_pdf_upload):
            raise Fast.HTTPException(status_code=400, detail="Report PDF upload must be a PDF file.")
        report_pdf = _save_report_pdf(slug, report_pdf_upload)
    site_db.projects.insert(
        Project(
            slug=slug,
            title=title,
            description=description,
            body=normalize_line_endings(body),
            url=url,
            report_pdf=report_pdf,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    logger.info("Created project %r", slug)
    return Fast.Redirect("/admin/work")


@router("/admin/work/{slug}/edit")
def get(slug: str, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.projects(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    return admin_layout(
        "Edit Project",
        Fast.H1("Edit Project"),
        _project_form(
            found[0], action=f"/admin/work/{slug}/edit", show_slug_field=False
        ),
    )


@router("/admin/work/{slug}/edit")
def post(
    slug: str,
    session,
    title: str,
    description: str,
    body: str,
    url: str = "",
    report_pdf_upload: Fast.UploadFile | None = None,
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.projects(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    report_pdf = found[0].report_pdf
    if _has_pdf_upload(report_pdf_upload):
        if not _looks_like_pdf(report_pdf_upload):
            raise Fast.HTTPException(status_code=400, detail="Report PDF upload must be a PDF file.")
        report_pdf = _save_report_pdf(slug, report_pdf_upload)
    site_db.projects.update(
        {
            "id": found[0].id,
            "title": title,
            "description": description,
            "body": normalize_line_endings(body),
            "url": url,
            "report_pdf": report_pdf,
        }
    )
    logger.info("Updated project %r", slug)
    return Fast.Redirect("/admin/work")


@router("/admin/work/{slug}/delete")
def post(slug: str, session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    found = site_db.projects(where="slug=?", where_args=[slug])
    if found:
        site_db.projects.delete(found[0].id)
        logger.warning("Deleted project %r", slug)
    return Fast.Redirect("/admin/work")


@router("/work/{slug}")
def get(slug: str):
    found = site_db.projects(where="slug=?", where_args=[slug])
    if not found:
        raise Fast.HTTPException(status_code=404)
    project = found[0]
    return site_layout(
        project.title,
        Fast.A("Work", href="/work", cls="back-link"),
        Fast.H1(project.title),
        Fast.P(project.description, cls="lede"),
        *(Fast.P(paragraph) for paragraph in project.body.split("\n\n") if paragraph),
        Fast.Div(
            Fast.A(project.url, href=project.url) if project.url else None,
            Fast.A("Download Report (PDF)", href=project.report_pdf)
            if project.report_pdf
            else None,
            cls="project-links",
        ),
    )


@router("/reports/{slug}.pdf")
def get(slug: str):
    path = _report_pdf_file_path(slug)
    if not path.is_file():
        raise Fast.HTTPException(status_code=404)
    return FileResponse(str(path), filename=f"{slug}.pdf", media_type=REPORT_PDF_CONTENT_TYPE)
