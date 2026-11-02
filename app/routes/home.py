from pathlib import Path
from random import sample

from fasthtml import common as Fast

from app.db import site_db
from app.layout import site_layout
from app.models import Product

router = Fast.APIRouter()

CYCLE_FRAME_COUNT = 10
SPOTLIGHT_SCRIPT_PATH = Path("static/js/spotlight.js")

# Both rendered server-side on every request; CSS then hides tiles past
# a per-breakpoint count via nth-child, so narrower screens show fewer
# without needing to infer viewport size server-side (see .tile-row--featured
# and .tile-row--blurb in site.css). Drawn from one combined random sample
# (see _product_samples) so the same product never appears in both rows.
FEATURED_SAMPLE_SIZE = 2
WORKBENCH_SAMPLE_SIZE = 6


def _reveal_stage() -> Fast.Div:
    """The fixed, full-viewport mark animation — the exact rings +
    crossfade technique from the mockup round's "Kaleidoscope Cycle"
    concept, scaled up and pinned behind the whole page. Shows through
    wherever a .window element below leaves no background in its way."""
    frames = (
        Fast.Img(
            src=f"/static/img/cycle/frame-{frame_number}.jpg",
            alt="",
            loading="eager",
            cls="frame-layer",
        )
        for frame_number in range(1, CYCLE_FRAME_COUNT + 1)
    )
    return Fast.Div(
        Fast.Div(
            Fast.Div(cls="ring"),
            Fast.Div(cls="ring ring--inner"),
            *frames,
            cls="reveal-mark",
        ),
        cls="reveal-stage",
        aria_hidden="true",
    )


def _spotlight_script() -> Fast.Script:
    """Drives the reveal-stage mark animation (see site.css's .frame-layer
    comment for why this is JS rather than a CSS animation). Only the
    home page renders .frame-layer elements, so this is scoped here
    rather than loaded site-wide via layout.py."""
    version = int(SPOTLIGHT_SCRIPT_PATH.stat().st_mtime)
    return Fast.Script(src=f"/static/js/spotlight.js?v={version}", defer=True)


def _window() -> Fast.Div:
    return Fast.Div(cls="window", aria_hidden="true")


def _section_mark(
    *, color: str, edge: str, anchor: str, image: str, size: str, opacity: float
) -> Fast.Div:
    """A faint, recolored mark fragment bled into a section's edge as a
    watermark. Rotates which jewel-tone variant and which accent color
    it uses, and which edge/anchor it bleeds from, section to section."""
    style = (
        f"width: {size}; height: {size}; "
        f"background-image: url('/static/img/{image}'); opacity: {opacity};"
    )
    return Fast.Div(
        cls=f"section-mark section-mark--{color} section-mark--{edge} section-mark--{anchor}",
        style=style,
        aria_hidden="true",
    )


def _product_tile(product: Product) -> Fast.A:
    return Fast.A(
        Fast.H3(product.name),
        Fast.P(product.description, cls="tile-blurb"),
        href=f"/products/{product.slug}",
        cls="tile tile--link",
    )


def _product_samples() -> tuple[list[Product], list[Product]]:
    """One random draw split into the home page's two rows — featured
    (small) then workbench (larger) — so the same product is never
    sampled into both."""
    products = site_db.products()
    combined = sample(products, k=min(FEATURED_SAMPLE_SIZE + WORKBENCH_SAMPLE_SIZE, len(products)))
    return combined[:FEATURED_SAMPLE_SIZE], combined[FEATURED_SAMPLE_SIZE:]


def _hero() -> Fast.Section:
    return Fast.Section(
        _section_mark(
            color="moss",
            edge="right",
            anchor="top",
            image="logo-variant-1.png",
            size="clamp(18rem, 36vw, 32rem)",
            opacity=0.26,
        ),
        Fast.Div(
            Fast.Div(
                Fast.H1("Formulas you can read, straight from the workbench."),
                Fast.P(
                    "For years, Kaleidoscopic Creations has reached people through "
                    "retail and boutique partners, who handled the telling while "
                    "Mrs. Kelsey handled the formulating. This site is her first "
                    "direct line to you — the same oils, butters, and essential "
                    "oils she's always worked with, with no one standing in between.",
                    cls="lede",
                ),
                Fast.A("See the lip balms", href="#products", cls="cta"),
                cls="hero-copy",
            ),
            cls="wrap",
        ),
        cls="hero opaque has-mark",
        id="home",
    )


def _products() -> Fast.Section:
    featured_sample, workbench_sample = _product_samples()
    return Fast.Section(
        _section_mark(
            color="berry",
            edge="left",
            anchor="bottom",
            image="logo-variant-2.png",
            size="clamp(16rem, 32vw, 28rem)",
            opacity=0.24,
        ),
        Fast.Div(
            Fast.H2("What's ready, and what's already working"),
            Fast.P(
                "Pulled live from what's currently in the catalog — not a "
                "fixed lineup, so what shows up here changes as new "
                "products go in.",
                cls="section-lede",
            ),
            Fast.Div(
                Fast.H3("Featured now", cls="group-heading"),
                Fast.Div(
                    *(_product_tile(product) for product in featured_sample),
                    cls="tile-row tile-row--featured",
                ),
                id="featured-products",
            )
            if featured_sample
            else None,
            Fast.Div(
                Fast.H3("Also from the workbench", cls="group-heading"),
                Fast.Div(
                    *(_product_tile(product) for product in workbench_sample),
                    cls="tile-row tile-row--blurb",
                ),
                id="workbench-products",
            )
            if workbench_sample
            else None,
            cls="wrap",
        ),
        cls="products opaque has-mark",
        id="products",
    )


def _private_label() -> Fast.Section:
    return Fast.Section(
        _section_mark(
            color="ochre",
            edge="right",
            anchor="top",
            image="logo-variant-3.png",
            size="clamp(16rem, 32vw, 28rem)",
            opacity=0.27,
        ),
        Fast.Div(
            Fast.H2("Private label is a revenue line, not a favor."),
            Fast.P(
                "If your business sells to people who'd pay more for "
                "something better under your own name, private label "
                "formulation is how you get there — your brand on the "
                "label, her formulation underneath it.",
                cls="lede-large",
            ),
            Fast.P(
                Fast.Strong("It already works."),
                " A spa partner carries her massage oil as a premium "
                "add-on — and charges more for the massage itself when a "
                "client adds it. That's one real example of a formula "
                "creating margin a service alone couldn't, not a projection.",
                cls="proof-point",
            ),
            Fast.A(
                "Talk to her about private label", href="/contact", cls="cta-light"
            ),
            cls="wrap",
        ),
        cls="services opaque has-mark",
        id="private-label",
    )


def _partners() -> Fast.Section:
    return Fast.Section(
        _section_mark(
            color="moss",
            edge="left",
            anchor="bottom",
            image="logo-variant-2.png",
            size="clamp(16rem, 30vw, 26rem)",
            opacity=0.25,
        ),
        Fast.Div(
            Fast.H2("Who she already makes for"),
            Fast.P(
                "Kaleidoscopic Creations has mostly sold through the "
                "businesses that carry it, not direct to the public.",
                cls="section-lede",
            ),
            Fast.Div(
                Fast.Div("Drop Dead Gorgeous", cls="partner-slot"),
                Fast.Div(
                    "More partners — details coming",
                    cls="partner-slot partner-slot--placeholder",
                ),
                Fast.Div(
                    "More partners — details coming",
                    cls="partner-slot partner-slot--placeholder",
                ),
                cls="partner-row",
            ),
            cls="wrap",
        ),
        cls="partners opaque has-mark",
        id="partners",
    )


def _about() -> Fast.Section:
    return Fast.Section(
        _section_mark(
            color="berry",
            edge="right",
            anchor="top",
            image="logo-variant-1.png",
            size="clamp(16rem, 30vw, 26rem)",
            opacity=0.24,
        ),
        Fast.Div(
            Fast.H2("Mrs. Kelsey, formulator"),
            Fast.Div(
                Fast.Div(
                    Fast.P(
                        "Mrs. Kelsey trained as a formulator, not a marketer. "
                        "For most of this brand's life, that's suited "
                        "everyone fine — the retail and boutique partners "
                        "carrying her work have handled the photos, the "
                        "displays, the pitch, while she's handled the "
                        "measuring, the testing, and getting each batch's "
                        "balance right."
                    ),
                    Fast.P(
                        "This site is her first push toward selling "
                        "directly to the public. What hasn't changed is "
                        "the approach underneath it: real plant oils and "
                        "butters, essential oils doing the scenting, made "
                        "in small batches by hand."
                    ),
                    cls="measure",
                ),
                Fast.Div(
                    Fast.H3("Credentials"),
                    Fast.Ul(
                        Fast.Li("[Certification — to be added]"),
                        Fast.Li("[Education / training — to be added]"),
                        Fast.Li("[Years of experience — to be added]"),
                    ),
                    cls="credentials",
                ),
                cls="about-grid",
            ),
            cls="wrap",
        ),
        cls="about opaque has-mark",
        id="about",
    )


@router("/")
def get():
    return site_layout(
        "Home",
        _spotlight_script(),
        _reveal_stage(),
        _hero(),
        _window(),
        _products(),
        _window(),
        _private_label(),
        _partners(),
        _window(),
        _about(),
    )
