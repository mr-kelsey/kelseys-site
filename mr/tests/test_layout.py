from pathlib import Path

from starlette.testclient import TestClient

from app.layout import DEFAULT_DESCRIPTION

STYLESHEET_PATH = Path("static/css/site.css")


def test_stylesheet_link_is_cache_busted_with_current_file_mtime(client: TestClient) -> None:
    response = client.get("/")
    expected_version = int(STYLESHEET_PATH.stat().st_mtime)
    assert f'/static/css/site.css?v={expected_version}"' in response.text


def test_footer_links_to_real_linkedin_profile(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="https://www.linkedin.com/in/mr-kelsey"' in response.text


def test_footer_links_to_real_github_profile(client: TestClient) -> None:
    response = client.get("/")
    assert 'href="https://github.com/mr-kelsey/"' in response.text


def test_page_has_og_title_matching_page_title(client: TestClient) -> None:
    response = client.get("/")
    assert '<meta property="og:title" content="Home — mr-kelsey">' in response.text


def test_page_without_explicit_description_uses_default_og_description(
    client: TestClient,
) -> None:
    response = client.get("/")
    assert f'<meta property="og:description" content="{DEFAULT_DESCRIPTION}">' in response.text
