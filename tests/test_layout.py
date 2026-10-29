from pathlib import Path

from starlette.testclient import TestClient

STYLESHEET_PATH = Path("static/css/site.css")


def test_stylesheet_link_is_cache_busted_with_current_file_mtime(client: TestClient) -> None:
    response = client.get("/")
    expected_version = int(STYLESHEET_PATH.stat().st_mtime)
    assert f'/static/css/site.css?v={expected_version}"' in response.text


def test_footer_links_to_contact_page(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="/contact"' in response.text


def test_footer_shows_site_title_in_copyright(client: TestClient) -> None:
    response = client.get("/")
    assert "Kaleidoscopic Creations" in response.text
