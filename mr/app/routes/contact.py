from datetime import datetime, timezone
from logging import getLogger
from fasthtml import common as Fast

from app.config import SiteConfig
from app.db import site_db
from app.email import EmailMessage, site_email_sender
from app.layout import site_layout
from app.models import ContactMessage

FALLBACK_TO_EMAIL = "site-owner@example.com"

router = Fast.APIRouter()
logger = getLogger(__name__)


def _contact_form() -> Fast.Form:
    return Fast.Form(
        Fast.Label("Name", Fast.Input(name="name", required=True)),
        Fast.Label("Email", Fast.Input(name="email", type="email", required=True)),
        Fast.Label("Message", Fast.Textarea(name="message", required=True)),
        Fast.Button("Send", type="submit"),
        method="post",
        action="/contact",
    )


@router("/contact")
def get(session):
    flash = session.pop("flash", None)
    return site_layout(
        "Contact",
        Fast.H1("Contact"),
        Fast.P(flash) if flash else None,
        _contact_form(),
    )


@router("/contact")
def post(name: str, email: str, message: str, session):
    site_db.contact_messages.insert(
        ContactMessage(
            name=name,
            email=email,
            message=message,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    config = SiteConfig()
    try:
        site_email_sender.send(
            EmailMessage(
                to=config.contact_to_email or FALLBACK_TO_EMAIL,
                subject=f"New contact form message from {name}",
                body=f"From: {name} <{email}>\n\n{message}",
            )
        )
    except Exception:
        logger.exception("Failed to send contact form notification email")
    session["flash"] = "Thanks — I'll be in touch."
    return Fast.Redirect("/contact")
