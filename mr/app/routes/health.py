from fasthtml import common as Fast

router = Fast.APIRouter()


@router("/healthz")
def get():
    return "ok"
