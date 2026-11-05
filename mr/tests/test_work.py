from starlette.testclient import TestClient

from app.db import Database
from app.models import Project


def test_returns_200_for_work_index(client: TestClient) -> None:
    response = client.get("/work")
    assert response.status_code == 200


def test_work_index_lists_seeded_project_title(client: TestClient, db: Database) -> None:
    db.projects.insert(Project(slug="hospital-cv", title="Hospital CV", description="d", url=""))
    response = client.get("/work")
    assert "Hospital CV" in response.text


def test_returns_200_for_known_project_slug(client: TestClient, db: Database) -> None:
    db.projects.insert(Project(slug="hospital-cv", title="Hospital CV", description="d", url=""))
    response = client.get("/work/hospital-cv")
    assert response.status_code == 200


def test_project_detail_shows_description(client: TestClient, db: Database) -> None:
    db.projects.insert(
        Project(slug="hospital-cv", title="Hospital CV", description="Reduces hospital waste via CV", url="")
    )
    response = client.get("/work/hospital-cv")
    assert "Reduces hospital waste via CV" in response.text


def test_returns_404_for_unknown_project_slug(client: TestClient) -> None:
    response = client.get("/work/does-not-exist")
    assert response.status_code == 404


def test_project_detail_shows_body_paragraph(client: TestClient, db: Database) -> None:
    db.projects.insert(
        Project(
            slug="hospital-cv",
            title="Hospital CV",
            description="d",
            body="First paragraph.\n\nSecond paragraph.",
            url="",
        )
    )
    response = client.get("/work/hospital-cv")
    assert "Second paragraph." in response.text


def test_project_detail_shows_report_download_link_when_set(client: TestClient, db: Database) -> None:
    db.projects.insert(
        Project(
            slug="hospital-cv",
            title="Hospital CV",
            description="d",
            url="",
            report_pdf="/static/projects/hospital-cv-report.pdf",
        )
    )
    response = client.get("/work/hospital-cv")
    assert '/static/projects/hospital-cv-report.pdf' in response.text


def test_project_detail_omits_report_download_link_when_unset(client: TestClient, db: Database) -> None:
    db.projects.insert(Project(slug="hospital-cv", title="Hospital CV", description="d", url=""))
    response = client.get("/work/hospital-cv")
    assert "Download Report" not in response.text
