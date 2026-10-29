from pathlib import Path

from fasthtml import common as Fast

STYLESHEET_PATH = Path("static/css/site.css")

NAV_LINKS: tuple[tuple[str, str], ...] = (
    ("Home", "/"),
    ("About", "/about"),
    ("Products", "/products"),
    ("Blog", "/blog"),
    ("Contact", "/contact"),
)


class Layout:
    """Wraps page content in the site's shared nav and footer shell.

    Deliberately bare/functional for now — no visual design pass yet.
    The real design work happens once the stakeholder is present to
    affirm choices (brand name "Kaleidoscopic Creations" confirmed, but
    colors/type/favicon are not)."""

    def __init__(self, site_title: str = "Kaleidoscopic Creations") -> None:
        self.site_title = site_title

    def _header(self) -> Fast.Header:
        return Fast.Header(
            Fast.A(self.site_title, href="/", cls="wordmark"),
            Fast.Nav(*(Fast.A(label, href=href) for label, href in NAV_LINKS)),
        )

    def _footer(self) -> Fast.Footer:
        return Fast.Footer(
            Fast.P(f"© {self.site_title}"),
            Fast.Nav(Fast.A("Contact", href="/contact")),
        )

    def _boundary(self, position: str) -> Fast.Div:
        return Fast.Div(cls=f"boundary boundary--{position}")

    def _stylesheet_href(self) -> str:
        version = int(STYLESHEET_PATH.stat().st_mtime)
        return f"/static/css/site.css?v={version}"

    def __call__(self, page_title: str, *content) -> tuple:
        return (
            Fast.Title(f"{page_title} — {self.site_title}"),
            Fast.Link(rel="stylesheet", href=self._stylesheet_href()),
            self._header(),
            self._boundary("top"),
            Fast.Main(Fast.Div(*content, cls="page")),
            self._boundary("bottom"),
            self._footer(),
        )


site_layout = Layout()
