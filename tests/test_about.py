from starlette.testclient import TestClient


def test_redirects_to_home_page_about_section(client: TestClient) -> None:
    response = client.get("/about", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/#about"
