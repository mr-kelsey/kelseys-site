from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()


@router("/")
def get():
    return site_layout(
        "Home",
        Fast.H1("Kaleidoscopic Creations"),
        Fast.P(
            "Placeholder — real homepage copy pending.",
            cls="lede",
        ),
        Fast.P(
            Fast.A("See the products", href="/products"),
            " or ",
            Fast.A("get in touch", href="/contact"),
            ".",
        ),
    )
