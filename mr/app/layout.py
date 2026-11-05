from pathlib import Path

from fasthtml import common as Fast

STYLESHEET_PATH = Path("static/css/site.css")

NAV_LINKS: tuple[tuple[str, str], ...] = (
    ("Home", "/"),
    ("About", "/about"),
    ("Resume", "/resume"),
    ("Work", "/work"),
    ("Blog", "/blog"),
    ("Contact", "/contact"),
)

FONT_LINKS: tuple[Fast.Link, ...] = (
    Fast.Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Fast.Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
    Fast.Link(
        rel="stylesheet",
        href=(
            "https://fonts.googleapis.com/css2?"
            "family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&"
            "family=IBM+Plex+Sans:wght@400;500;600&"
            "family=IBM+Plex+Mono:wght@400;500&"
            "display=swap"
        ),
    ),
)


class Layout:
    """Wraps page content in the site's shared nav and footer shell."""

    def __init__(self, site_title: str = "mr-kelsey") -> None:
        self.site_title = site_title

    def _header(self) -> Fast.Header:
        return Fast.Header(
            Fast.A(self.site_title, href="/", cls="wordmark"),
            Fast.Nav(*(Fast.A(label, href=href) for label, href in NAV_LINKS)),
        )

    def _footer(self) -> Fast.Footer:
        return Fast.Footer(
            Fast.P(f"© {self.site_title}"),
            Fast.Nav(
                Fast.A("LinkedIn", href="https://www.linkedin.com/in/mr-kelsey"),
                Fast.A("GitHub", href="https://github.com/mr-kelsey/"),
                Fast.A("Email", href="/contact"),
            ),
        )

    def _boundary(self, position: str) -> Fast.Div:
        return Fast.Div(cls=f"boundary boundary--{position}")

    def _stylesheet_href(self) -> str:
        version = int(STYLESHEET_PATH.stat().st_mtime)
        return f"/static/css/site.css?v={version}"

    def __call__(self, page_title: str, *content) -> tuple:
        return (
            Fast.Title(f"{page_title} — {self.site_title}"),
            Fast.Link(rel="icon", href="/static/img/favicon.png", type="image/png"),
            *FONT_LINKS,
            Fast.Link(rel="stylesheet", href=self._stylesheet_href()),
            self._header(),
            self._boundary("top"),
            Fast.Main(Fast.Div(*content, cls="page")),
            self._boundary("bottom"),
            self._footer(),
        )


site_layout = Layout()
