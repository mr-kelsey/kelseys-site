from pathlib import Path

from starlette.testclient import TestClient

SCRATCH_FILE = Path("scripts/test_security_scratch.txt")


def test_non_whitelisted_extension_is_not_served_even_if_file_exists(
    client: TestClient,
) -> None:
    SCRATCH_FILE.write_text("this should never be publicly reachable")
    try:
        response = client.get(f"/{SCRATCH_FILE}")
        assert response.status_code == 404
    finally:
        SCRATCH_FILE.unlink()


def test_whitelisted_static_asset_is_still_served(client: TestClient) -> None:
    response = client.get("/static/css/site.css")
    assert response.status_code == 200
