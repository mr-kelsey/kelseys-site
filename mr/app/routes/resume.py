from dataclasses import dataclass

from fasthtml import common as Fast

from app.layout import site_layout

router = Fast.APIRouter()

TAGLINE = "Cybersecurity Analyst (CySA+) | Applied AI/ML"

SUMMARY = (
    "A decade owning and operating a licensed cannabis retail delivery business in "
    "California — one of the most heavily regulated retail environments in the "
    "country — built a practical foundation in compliance and security before "
    "formalizing it with a BS in Cybersecurity and a CompTIA CySA+. Since completing "
    "an MS in Applied AI, that security judgment has carried into independent AI/ML "
    "contract work, including a computer vision system recovering $150K/month in "
    "missorted medical waste. The combination of real regulatory experience, formal "
    "security training, and applied AI/ML work is uncommon in either field alone."
)


@dataclass
class ExperienceEntry:
    role: str
    org: str
    dates: str
    bullets: tuple[str, ...]
    location: str = ""


EXPERIENCE: tuple[ExperienceEntry, ...] = (
    ExperienceEntry(
        role="Independent Contractor",
        org="TMG EnviroTech Systems",
        dates="Mar 2024 – Present",
        location="Remote",
        bullets=(
            "Designed and deployed a computer vision system identifying and "
            "correcting waste-sorting errors, recovering $150K/month in missorted "
            "medical waste",
            "Enforce HIPAA compliance, least-privilege access controls, and secure "
            "data pipelines",
        ),
    ),
    ExperienceEntry(
        role="Operations Manager",
        org="Schupan",
        dates="Mar 2024 – Present",
        location="Field-based · Wixom, MI",
        bullets=(
            "Sole on-site representative for a portfolio of recycling and "
            "sustainability clients; oversee materials-handling procedures and "
            "logistics, and resolve equipment and operational issues in real time "
            "to meet service commitments regardless of site conditions",
            "Track and calculate landfill diversion rates from truck weight data "
            "across managed accounts",
            "Achieved an 88.75% average diversion rate across 581 events, "
            "including 30 tons diverted at a single event",
            "Supervise on-site crew performance and equipment utilization during "
            "field operations",
            "Lead the company's first international expansion, into Canada, in 2026",
        ),
    ),
    ExperienceEntry(
        role="Independent Contractor",
        org="DataAnnotation.tech",
        dates="Aug 2024 – Jun 2026",
        location="Remote",
        bullets=(
            "Performed RLHF (reinforcement learning from human feedback) data "
            "annotation and model-evaluation work supporting AI training pipelines",
            "Completed 1,000+ tasks across code, math, and security domains, "
            "specializing in sub-agent tool calling",
        ),
    ),
    ExperienceEntry(
        role="Structured Cabling & Security Systems Technician",
        org="Moss Telecommunications",
        dates="Jan 2023 – Nov 2024",
        bullets=(
            "Ran and terminated structured cabling; configured and installed "
            "network switches, IP cameras, and NVRs; installed A/V systems for "
            "networked security infrastructure deployments",
        ),
    ),
    ExperienceEntry(
        role="Owner / Operator",
        org="BNG Deliveries",
        dates="Jun 2012 – Dec 2022",
        location="California",
        bullets=(
            "Owned and operated a licensed cannabis retail delivery business for "
            "over 10 years",
            "Responsible for regulatory compliance, inventory security, and "
            "operational security under continuous state licensing oversight",
        ),
    ),
    ExperienceEntry(
        role="Independent Contractor",
        org="National Weather Service",
        dates="Sep 2022 – Nov 2022",
        location="Remote",
        bullets=(
            "Developed sensor-testing software for NWS sensor systems, producing "
            "the evidence used in the congressional approval process",
            "Validated 89 sensors and enabled continuous data monitoring, "
            "delivering on schedule",
        ),
    ),
)


@dataclass
class EducationEntry:
    name: str
    org: str
    dates: str
    detail: str = ""


EDUCATION: tuple[EducationEntry, ...] = (
    EducationEntry(
        name="MS, Applied Artificial Intelligence",
        org="University of San Diego",
        dates="Jan 2025 – Aug 2026",
        detail=(
            "Capstone: Out of the Park — Predicting the Increase in Foot Traffic "
            "Caused by Live Events. Built and deployed on AWS a graph neural "
            "network (GNN) that forecasts foot traffic from real-world event data; "
            "achieved 13% MAPE"
        ),
    ),
    EducationEntry(
        name="BS, Cybersecurity",
        org="Western Governors University",
        dates="Dec 2020 – Nov 2022",
    ),
)


@dataclass
class CertificationEntry:
    name: str
    dates: str
    lapsed: bool = False


CERTIFICATIONS: tuple[CertificationEntry, ...] = (
    CertificationEntry("CompTIA Cybersecurity Analyst (CySA+)", "Jul 2022 – Jul 2028"),
    CertificationEntry("CompTIA PenTest+", "Feb 2021 – Feb 2027"),
    CertificationEntry("CompTIA Security+", "Sep 2020 – Jul 2028"),
    CertificationEntry("CompTIA Network+", "Jan 2022 – Jul 2028"),
    CertificationEntry("CompTIA A+", "Jul 2021 – Jul 2028"),
    CertificationEntry("CompTIA Project+", "Apr 2022 – No expiration"),
    CertificationEntry("GIAC Cloud Security Essentials (GCLD)", "Oct 2023 – Oct 2027"),
    CertificationEntry(
        "ISC2 Systems Security Certified Practitioner (SSCP)",
        "Jan 2023 – Jan 2026",
        lapsed=True,
    ),
    CertificationEntry(
        "GIAC Foundational Cybersecurity Technologies (GFACT)",
        "Sep 2022 – Sep 2026",
        lapsed=True,
    ),
)


@dataclass
class SkillGroup:
    label: str
    items: tuple[str, ...]


SKILLS: tuple[SkillGroup, ...] = (
    SkillGroup(
        "Security & Compliance",
        ("Cybersecurity", "Governance Risk & Compliance (GRC)"),
    ),
    SkillGroup("Networking", ("Network Security", "Network Administration")),
    SkillGroup(
        "Applied AI/ML",
        ("Machine Learning", "Computer Vision", "Artificial Intelligence"),
    ),
    SkillGroup("Operations", ("Regulatory Compliance", "Operations Management")),
)


def _row_head(title: str, subtitle: str, dates: str) -> Fast.Div:
    return Fast.Div(
        Fast.Span(
            Fast.Span(title, cls="resume-row-title"),
            " — ",
            Fast.Span(subtitle, cls="resume-row-subtitle"),
        ),
        Fast.Span(dates, cls="resume-dates"),
        cls="resume-row-head",
    )


def _experience_row(entry: ExperienceEntry) -> Fast.Div:
    children = [_row_head(entry.role, entry.org, entry.dates)]
    if entry.location:
        children.append(Fast.P(entry.location, cls="resume-location"))
    children.append(
        Fast.Ul(*(Fast.Li(bullet) for bullet in entry.bullets), cls="resume-bullets")
    )
    return Fast.Div(*children, cls="resume-row")


def _education_row(entry: EducationEntry) -> Fast.Div:
    children = [_row_head(entry.name, entry.org, entry.dates)]
    if entry.detail:
        children.append(Fast.P(entry.detail, cls="resume-detail"))
    return Fast.Div(*children, cls="resume-row")


def _certification_row(entry: CertificationEntry) -> Fast.Div:
    name_parts = [Fast.Span(entry.name, cls="resume-row-title")]
    if entry.lapsed:
        name_parts.append(Fast.Span("lapsed", cls="resume-lapsed"))
    return Fast.Div(
        Fast.Span(*name_parts),
        Fast.Span(entry.dates, cls="resume-dates"),
        cls="resume-row resume-row--compact",
    )


def _skill_group_row(group: SkillGroup) -> Fast.Div:
    return Fast.Div(
        Fast.Span(group.label, cls="resume-skill-label"),
        Fast.Span(", ".join(group.items), cls="resume-skill-list"),
        cls="resume-skill-group",
    )


@router("/resume")
def get():
    return site_layout(
        "Resume",
        Fast.H1("Johnathan Kelsey"),
        Fast.P(TAGLINE, cls="lede"),
        Fast.Section(Fast.H2("Summary"), Fast.P(SUMMARY), cls="resume-section"),
        Fast.Section(
            Fast.H2("Experience"),
            *(_experience_row(entry) for entry in EXPERIENCE),
            cls="resume-section",
        ),
        Fast.Section(
            Fast.H2("Education"),
            *(_education_row(entry) for entry in EDUCATION),
            cls="resume-section",
        ),
        Fast.Section(
            Fast.H2("Certifications"),
            *(_certification_row(entry) for entry in CERTIFICATIONS),
            cls="resume-section",
        ),
        Fast.Section(
            Fast.H2("Skills"),
            *(_skill_group_row(group) for group in SKILLS),
            cls="resume-section",
        ),
    )
