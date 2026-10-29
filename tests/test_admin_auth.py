import logging
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from app.auth import MAX_FAILED_LOGIN_ATTEMPTS
from conftest import ADMIN_PASSWORD_FOR_TESTS

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


def _fail_login(client: TestClient, times: int) -> None:
    for _ in range(times):
        client.post("/admin/login", data={"password": "wrong"})


def test_admin_login_page_returns_200(client: TestClient) -> None:
    response = client.get("/admin/login")
    assert response.status_code == 200


def test_admin_login_page_shows_password_field(client: TestClient) -> None:
    response = client.get("/admin/login")
    assert 'name="password"' in response.text


def test_post_admin_login_with_correct_password_redirects_to_dashboard(
    client: TestClient,
) -> None:
    response = client.post(
        "/admin/login",
        data={"password": ADMIN_PASSWORD_FOR_TESTS},
        follow_redirects=False,
    )
    assert response.headers["location"] == "/admin"


def test_post_admin_login_with_wrong_password_shows_error(client: TestClient) -> None:
    response = client.post("/admin/login", data={"password": "wrong"})
    assert "Incorrect password" in response.text


def test_post_admin_login_with_wrong_password_does_not_set_session(
    client: TestClient,
) -> None:
    client.post("/admin/login", data={"password": "wrong"})
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code in (302, 303, 307)


def test_get_admin_dashboard_redirects_when_not_authenticated(
    client: TestClient,
) -> None:
    response = client.get("/admin", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_dashboard_returns_200_when_authenticated(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin")
    assert response.status_code == 200


def test_post_admin_logout_clears_session(admin_client: TestClient) -> None:
    admin_client.post("/admin/logout")
    response = admin_client.get("/admin", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_admin_dashboard_shows_logout_control(admin_client: TestClient) -> None:
    response = admin_client.get("/admin")
    assert 'action="/admin/logout"' in response.text


def test_admin_login_allows_correct_password_below_lockout_threshold(
    client: TestClient,
) -> None:
    _fail_login(client, MAX_FAILED_LOGIN_ATTEMPTS - 1)
    response = client.post(
        "/admin/login",
        data={"password": ADMIN_PASSWORD_FOR_TESTS},
        follow_redirects=False,
    )
    assert response.headers["location"] == "/admin"


def test_admin_login_blocks_correct_password_at_lockout_threshold(
    client: TestClient,
) -> None:
    _fail_login(client, MAX_FAILED_LOGIN_ATTEMPTS)
    response = client.post(
        "/admin/login",
        data={"password": ADMIN_PASSWORD_FOR_TESTS},
        follow_redirects=False,
    )
    assert response.status_code == 200


def test_admin_login_shows_lockout_message_at_threshold(client: TestClient) -> None:
    _fail_login(client, MAX_FAILED_LOGIN_ATTEMPTS)
    response = client.post(
        "/admin/login", data={"password": ADMIN_PASSWORD_FOR_TESTS}
    )
    assert "Too many attempts" in response.text


def test_successful_login_is_logged(
    client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.INFO)
    client.post("/admin/login", data={"password": ADMIN_PASSWORD_FOR_TESTS})
    assert "login succeeded" in caplog.text.lower()


def test_failed_login_is_logged(
    client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.WARNING)
    client.post("/admin/login", data={"password": "wrong"})
    assert "login failed" in caplog.text.lower()


def test_lockout_block_is_logged(
    client: TestClient, caplog: "LogCaptureFixture"
) -> None:
    caplog.set_level(logging.WARNING)
    _fail_login(client, MAX_FAILED_LOGIN_ATTEMPTS)
    caplog.clear()
    client.post("/admin/login", data={"password": ADMIN_PASSWORD_FOR_TESTS})
    assert "lockout" in caplog.text.lower()


def test_admin_login_success_clears_failed_attempt_count(client: TestClient) -> None:
    _fail_login(client, MAX_FAILED_LOGIN_ATTEMPTS - 1)
    client.post("/admin/login", data={"password": ADMIN_PASSWORD_FOR_TESTS})
    client.post("/admin/logout")
    _fail_login(client, MAX_FAILED_LOGIN_ATTEMPTS - 1)
    response = client.post(
        "/admin/login",
        data={"password": ADMIN_PASSWORD_FOR_TESTS},
        follow_redirects=False,
    )
    assert response.headers["location"] == "/admin"
