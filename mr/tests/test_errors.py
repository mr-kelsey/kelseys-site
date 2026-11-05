from starlette.testclient import TestClient


def test_unknown_route_returns_404(client: TestClient) -> None:
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404


def test_unknown_route_404_page_uses_site_stylesheet(client: TestClient) -> None:
    response = client.get("/this-route-does-not-exist")
    assert "site.css" in response.text


def test_unknown_route_404_page_shows_heading(client: TestClient) -> None:
    response = client.get("/this-route-does-not-exist")
    assert "<h1>404</h1>" in response.text


def test_unknown_work_slug_404_page_uses_site_stylesheet(client: TestClient) -> None:
    response = client.get("/work/does-not-exist")
    assert "site.css" in response.text
