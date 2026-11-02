from pathlib import Path

from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()

CYCLE_FRAME_COUNT = 10
SPOTLIGHT_SCRIPT_PATH = Path("static/js/spotlight.js")

LIP_BALM_BASE: tuple[str, ...] = (
    "White Beeswax",
    "Kokum Butter",
    "Coconut Oil",
    "Avocado Oil",
    "Macadamia Oil",
    "Emu Oil",
    "Vit E Oil",
    "CBD Raw",
)
LIP_BALM_SCENT: tuple[str, ...] = ("Frankincense EO", "Melaleuca EO", "Lavender EO")
BRIGHT_LIP_BALM_SCENT: tuple[str, ...] = (
    "Grapefruit EO",
    "Wild Orange EO",
    "Tangerine EO",
    "Peppermint EO",
)


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


def _ingredient_table(
    caption: str, base: tuple[str, ...], scent: tuple[str, ...]
) -> Fast.Table:
    """A specimen-style ingredient list — names only, grouped by Base
    and Scent, deliberately no weight percentages (those are hers)."""
    return Fast.Table(
        Fast.Caption(caption, cls="sr-only"),
        Fast.Thead(Fast.Tr(Fast.Th("Ingredient", scope="col"))),
        Fast.Tbody(
            Fast.Tr(Fast.Th("Base", scope="colgroup"), cls="group-row"),
            *(Fast.Tr(Fast.Th(name, scope="row")) for name in base),
            Fast.Tr(Fast.Th("Scent", scope="colgroup"), cls="group-row"),
            *(Fast.Tr(Fast.Th(name, scope="row")) for name in scent),
        ),
        cls="ingredient-table",
    )


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
                "The two balms are built from one base and finished with "
                "different scent blends. A few more things she makes aren't "
                "balms at all — here's what they are, honestly, without a "
                "formula sheet to show for it yet.",
                cls="section-lede",
            ),
            Fast.H3("The lip balms", cls="group-heading"),
            Fast.Div(
                Fast.Article(
                    Fast.H3("Lip Balm"),
                    Fast.P("woodsy-floral", cls="tile-character moss"),
                    _ingredient_table(
                        "Lip Balm ingredients", LIP_BALM_BASE, LIP_BALM_SCENT
                    ),
                    cls="tile",
                ),
                Fast.Article(
                    Fast.H3("Bright Lip Balm"),
                    Fast.P("citrus-bright", cls="tile-character ochre"),
                    _ingredient_table(
                        "Bright Lip Balm ingredients",
                        LIP_BALM_BASE,
                        BRIGHT_LIP_BALM_SCENT,
                    ),
                    cls="tile",
                ),
                cls="tile-row",
            ),
            Fast.H3("Also from the workbench", cls="group-heading"),
            Fast.Div(
                Fast.Article(
                    Fast.H3("Facial Regimen"),
                    Fast.P(
                        "A multi-step regimen for the face — a short ritual of "
                        "products meant to be used together, not a single jar. "
                        "The full write-up is still being put together for "
                        "the site.",
                        cls="tile-blurb",
                    ),
                    cls="tile",
                ),
                Fast.Article(
                    Fast.H3("After-Tattoo Care"),
                    Fast.P(
                        "A dedicated aftercare product, made for the days "
                        "right after a new tattoo.",
                        cls="tile-blurb",
                    ),
                    cls="tile",
                ),
                Fast.Article(
                    Fast.H3("Massage Oil"),
                    Fast.P(
                        "Sold to a spa partner, where it's now offered as a "
                        "premium add-on during treatments.",
                        cls="tile-blurb",
                    ),
                    cls="tile",
                ),
                cls="tile-row tile-row--blurb",
            ),
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
