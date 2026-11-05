from starlette.testclient import TestClient


def test_returns_200_for_resume_page(client: TestClient) -> None:
    response = client.get("/resume")
    assert response.status_code == 200


def test_resume_page_links_to_resume_pdf(client: TestClient) -> None:
    response = client.get("/resume")
    assert 'href="/resume.pdf"' in response.text


def test_resume_page_has_no_placeholder_copy(client: TestClient) -> None:
    response = client.get("/resume")
    assert "Placeholder" not in response.text


def test_resume_page_shows_real_job_title(client: TestClient) -> None:
    response = client.get("/resume")
    assert "AI Security Engineer" in response.text


def test_returns_200_for_resume_pdf(client: TestClient) -> None:
    response = client.get("/resume.pdf")
    assert response.status_code == 200


def test_resume_pdf_has_pdf_content_type(client: TestClient) -> None:
    response = client.get("/resume.pdf")
    assert response.headers["content-type"] == "application/pdf"


def test_resume_pdf_has_attachment_disposition(client: TestClient) -> None:
    response = client.get("/resume.pdf")
    assert "attachment" in response.headers["content-disposition"]
