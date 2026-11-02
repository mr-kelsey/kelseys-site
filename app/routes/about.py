from fasthtml import common as Fast

router = Fast.APIRouter()


@router("/about")
def get():
    """About was folded into the home page's #about section — this route
    stays only so anything still linking directly to /about keeps working."""
    return Fast.Redirect("/#about")
