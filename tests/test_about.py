from starlette.testclient import TestClient


def test_returns_200_for_about_page(client: TestClient) -> None:
    response = client.get("/about")
    assert response.status_code == 200


def test_about_page_includes_nav_link_to_home(client: TestClient) -> None:
    response = client.get("/about")
    assert 'href="/"' in response.text
