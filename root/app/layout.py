from pathlib import Path

from fasthtml import common as Fast

STYLESHEET_PATH = Path("static/css/site.css")

NAV_LINKS: tuple[tuple[str, str], ...] = (
    ("Home", "/"),
    ("Recipes", "/recipes"),
    ("Random recipe", "/recipes/random"),
)

FONT_LINKS: tuple[Fast.Link, ...] = (
    Fast.Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Fast.Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
    Fast.Link(
        rel="stylesheet",
        href=(
            "https://fonts.googleapis.com/css2?"
            "family=Besley:wght@500;600;700&"
            "family=Public+Sans:wght@400;500;600&"
            "family=IBM+Plex+Mono:wght@400;500&"
            "display=swap"
        ),
    ),
)


class Layout:
    "Wraps page content in the site's shared nav and footer shell."

    def __init__(self, site_title: str = "kelseys.site") -> None:
        self.site_title = site_title

    def _header(self) -> Fast.Header:
        return Fast.Header(
            Fast.Div(
                Fast.Span(self.site_title, cls="wordmark"),
                Fast.Nav(
                    *(Fast.A(label, href=href) for label, href in NAV_LINKS),
                    aria_label="Primary",
                ),
                cls="wrap",
            ),
            cls="site-nav",
        )

    def _footer(self) -> Fast.Footer:
        return Fast.Footer(
            Fast.Nav(
                *(Fast.A(label, href=href) for label, href in NAV_LINKS),
                aria_label="Footer",
            ),
            cls="wrap",
        )

    def _stylesheet_href(self) -> str:
        version = int(STYLESHEET_PATH.stat().st_mtime)
        return f"/static/css/site.css?v={version}"

    def __call__(self, page_title: str, *content) -> tuple:
        return (
            Fast.Title(f"{page_title} — {self.site_title}"),
            *FONT_LINKS,
            Fast.Link(rel="stylesheet", href=self._stylesheet_href()),
            Fast.A("Skip to content", href="#main-content", cls="skip-link"),
            self._header(),
            Fast.Main(Fast.Div(*content, cls="page"), id="main-content"),
            self._footer(),
        )


site_layout = Layout()
