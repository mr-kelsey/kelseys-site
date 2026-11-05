from starlette.testclient import TestClient


def test_robots_txt_returns_200(client: TestClient) -> None:
    response = client.get("/robots.txt")
    assert response.status_code == 200


def test_robots_txt_disallows_admin(client: TestClient) -> None:
    response = client.get("/robots.txt")
    assert "Disallow: /admin" in response.text
