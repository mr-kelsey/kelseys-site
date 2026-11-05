from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()


@router("/")
def get():
    return site_layout(
        "Home",
        Fast.Div(
            Fast.H1("kelseys.site"),
            Fast.P("A recipe book, searchable by name, ingredient, or servings."),
            Fast.Div(
                Fast.A("Browse recipes", href="/recipes", cls="button"),
                Fast.A("I don't know what to cook", href="/recipes/random", cls="button button--secondary"),
                cls="home-actions",
            ),
            cls="home-hero",
        ),
    )
