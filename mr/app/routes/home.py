from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()


@router("/")
def get():
    return site_layout(
        "Home",
        Fast.H1("Welcome, and thanks for stopping by!"),
        Fast.P(
            "A master's degree in AI and a BS in cybersecurity, "
            "plus a decade of software engineering contract work. "
            "On the soft skill side, I've owned my own business and "
            "was a former general manager for a multinational "
            "corporation. Most hiring managers get nervous about a "
            "candidate with limited time on the org chart.  Those who "
            "don't recognize what it means: a self-starter with limited "
            "need for tedious oversight. You just tell me what you need, "
            "and I get it done.  Now, let's get to business and find "
            "those failure points that are costing you money.",
            cls="lede",
        ),
        Fast.P(
            Fast.A("See the work", href="/work"),
            " or ",
            Fast.A("read the résumé", href="/resume"),
            ".",
        ),
    )
