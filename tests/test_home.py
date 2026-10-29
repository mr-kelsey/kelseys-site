from starlette.testclient import TestClient


def test_returns_200_for_home_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_home_page_includes_nav_link_to_products(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/products"' in response.text


def test_home_page_includes_nav_link_to_about(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/about"' in response.text


def test_home_page_includes_nav_link_to_contact(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/contact"' in response.text
