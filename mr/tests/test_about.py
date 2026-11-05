from starlette.testclient import TestClient


def test_returns_200_for_about_page(client: TestClient) -> None:
    response = client.get("/about")
    assert response.status_code == 200


def test_about_page_includes_nav_link_to_home(client: TestClient) -> None:
    response = client.get("/about")
    assert 'href="/"' in response.text


def test_about_page_no_longer_shows_placeholder_copy(client: TestClient) -> None:
    response = client.get("/about")
    assert "Placeholder bio" not in response.text


def test_about_page_includes_founder_background(client: TestClient) -> None:
    response = client.get("/about")
    assert "cannabis" in response.text
