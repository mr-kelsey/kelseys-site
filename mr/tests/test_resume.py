from starlette.testclient import TestClient


def test_returns_200_for_resume_page(client: TestClient) -> None:
    response = client.get("/resume")
    assert response.status_code == 200


def test_resume_page_has_no_placeholder_copy(client: TestClient) -> None:
    response = client.get("/resume")
    assert "Placeholder" not in response.text


def test_resume_page_shows_real_job_title(client: TestClient) -> None:
    response = client.get("/resume")
    assert "Cybersecurity Analyst (CySA+) | Applied AI/ML" in response.text


def test_resume_page_shows_schupan_diversion_rate(client: TestClient) -> None:
    response = client.get("/resume")
    assert "88.75%" in response.text


def test_resume_page_shows_capstone_project(client: TestClient) -> None:
    response = client.get("/resume")
    assert "Out of the Park" in response.text


def test_resume_page_has_no_pdf_download_link(client: TestClient) -> None:
    response = client.get("/resume")
    assert 'href="/resume.pdf"' not in response.text


def test_resume_pdf_route_no_longer_exists(client: TestClient) -> None:
    response = client.get("/resume.pdf")
    assert response.status_code == 404
