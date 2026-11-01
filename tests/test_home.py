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


def test_home_page_includes_fixed_reveal_layer(client: TestClient) -> None:
    response = client.get("/")
    assert 'class="reveal-stage"' in response.text


def test_home_page_lists_a_real_lip_balm_ingredient(client: TestClient) -> None:
    response = client.get("/")
    assert "White Beeswax" in response.text


def test_home_page_does_not_show_ingredient_percentages(client: TestClient) -> None:
    response = client.get("/")
    assert "21.2%" not in response.text


def test_home_page_pitches_private_label_to_businesses(client: TestClient) -> None:
    response = client.get("/")
    assert "Private label is a revenue line" in response.text


def test_home_page_names_a_real_partner_company(client: TestClient) -> None:
    response = client.get("/")
    assert "Drop Dead Gorgeous" in response.text


def test_home_page_marks_credentials_as_placeholder(client: TestClient) -> None:
    response = client.get("/")
    assert "to be added" in response.text
