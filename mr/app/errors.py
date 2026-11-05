from fasthtml import common as Fast

from app.layout import site_layout


def not_found(request, exc):
    return site_layout(
        "Not Found",
        Fast.H1("404"),
        Fast.P("That page no longer exists — or, perhaps, never existed to begin with. Try the nav, or head back home."),
        Fast.A("Back home", href="/"),
    )
