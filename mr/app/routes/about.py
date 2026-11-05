from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()


BIO_PARAGRAPHS: tuple[str, ...] = (
    "Before I was writing Python, I was running "
    "structured cable through hospital ceilings and wiring up industrial PLCs — "
    "before that, I built, ran, and sold a licensed cannabis delivery business in "
    "a state that made you earn every inch of compliance. Thirteen employees, a "
    "banking relationship nobody thought a business like that would get, and a "
    "decade of learning that the hard problems are never the technical ones — "
    "they're the ones where a mistake costs someone real money or their trust in you.",
    "That instinct is what pulled me toward security. I went back for a B.S. in "
    "Cybersecurity, picked up CySA+, PenTest+, SSCP, and a stack of other certs, "
    "and started asking the same question of every system I touched: what happens "
    "when this fails, and who's watching for it. From there, an M.S. in Applied AI "
    "was the obvious next step — the systems worth securing now are the ones making "
    "decisions on their own.",
    "Most of my career has run on contracts rather than a single employer's org "
    "chart. I've built the sensor-testing software the National Weather Service "
    "used to validate 89 units for congressional approval. I've spent two years as "
    "the lead engineer on a computer vision system that catches $150K a month in "
    "medical waste before it happens. I've ranked LLM outputs for RLHF and have "
    "plenty of hands-on data experience putting projects together for my master's "
    "degree. Right now, I split my time between AI security "
    "work and sustainability engineering — designing waste-diversion plans that "
    "have kept 72% of material out of landfills across 581 events.",
    "The common thread, if there is one: I go where the failure mode is expensive "
    "and figure out how to catch it earlier. 'Security' is just that instinct with "
    "a job title.",
)


@router("/about")
def get():
    return site_layout(
        "About",
        Fast.H1("About"),
        *(Fast.P(paragraph) for paragraph in BIO_PARAGRAPHS),
    )
