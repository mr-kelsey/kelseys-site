from pathlib import Path

from fasthtml import common as Fast

STYLESHEET_PATH = Path("static/css/site.css")

NAV_LINKS: tuple[tuple[str, str], ...] = (
    ("Home", "/"),
    ("About", "/#about"),
    ("Products", "/products"),
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
            "family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&"
            "family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&"
            "family=Space+Mono:wght@400;700&"
            "display=swap"
        ),
    ),
)


class Layout:
    """Wraps page content in the site's shared nav and footer shell.

    Visual identity is "Apothecary Reveal" — moss/berry/ochre on bone
    paper, Fraunces + Source Serif 4 + Space Mono — chosen after a round
    of mockups reviewed with the stakeholder. The home page additionally
    renders a fixed, full-viewport mark animation behind its content
    (app/routes/home.py), shown through transparent "window" gaps only
    it currently has; other pages stay fully opaque so the layer never
    becomes visible there."""

    def __init__(self, site_title: str = "Kaleidoscopic Creations") -> None:
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
            cls="site-nav opaque",
        )

    def _footer(self) -> Fast.Footer:
        return Fast.Footer(
            Fast.Div(
                cls=(
                    "section-mark section-mark--ochre "
                    "section-mark--left section-mark--bottom"
                ),
                style=(
                    "width: clamp(14rem, 26vw, 22rem); "
                    "height: clamp(14rem, 26vw, 22rem); "
                    "background-image: url('/static/img/logo-variant-2.png'); "
                    "opacity: 0.22;"
                ),
                aria_hidden="true",
            ),
            Fast.Div(
                Fast.Nav(
                    *(Fast.A(label, href=href) for label, href in NAV_LINKS),
                    aria_label="Footer",
                ),
                Fast.P(
                    "Questions about a formula, or interested in private label? "
                    "That's what Contact is for. Kaleidoscopic Creations is "
                    "hand-blended by Mrs. Kelsey.",
                    cls="contact-line",
                ),
                cls="wrap",
            ),
            cls="opaque has-mark",
            id="contact",
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
            Fast.A("Skip to content", href="#main-content", cls="skip-link"),
            self._header(),
            self._boundary("top"),
            Fast.Main(Fast.Div(*content, cls="page"), id="main-content"),
            self._boundary("bottom"),
            self._footer(),
        )


site_layout = Layout()
