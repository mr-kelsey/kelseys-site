from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()


@router("/about")
def get():
    return site_layout(
        "About",
        Fast.Div(
            Fast.H1("About"),
            Fast.P("Placeholder bio — real company story pending."),
            cls="simple-page",
        ),
    )
