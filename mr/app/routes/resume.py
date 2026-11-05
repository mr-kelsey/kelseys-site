from fasthtml import common as Fast
from starlette.responses import FileResponse

from app.layout import site_layout

RESUME_PDF_PATH = "static/resume.pdf"

router = Fast.APIRouter()


@router("/resume")
def get():
    return site_layout(
        "Resume",
        Fast.H1("Resume"),
        Fast.P(
            "Johnathan Kelsey — AI Security Engineer | Machine Learning Engineer | "
            "Cybersecurity Analyst. Kalamazoo, MI (open to remote).",
            cls="lede",
        ),
        Fast.P(
            "M.S. in Applied Artificial Intelligence (University of San Diego, 2026) "
            "and a B.S. in Cybersecurity and Information Assurance (WGU, 2022), "
            "CompTIA CySA+ certified. Five-plus years of independent contract work: "
            "sensor-testing software for the National Weather Service, a computer "
            "vision system that recovers $150K a month in medical waste, RLHF data "
            "work, and sustainability engineering — on top of a decade running "
            "network infrastructure and a licensed business before any of that."
        ),
        Fast.P(Fast.A("Download PDF", href="/resume.pdf")),
    )


@router("/resume.pdf")
def get():
    return FileResponse(
        RESUME_PDF_PATH, filename="resume.pdf", media_type="application/pdf"
    )
