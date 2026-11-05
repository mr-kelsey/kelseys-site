from collections import defaultdict
from collections.abc import Callable
from hmac import compare_digest
from time import monotonic

from fasthtml import common as Fast

from app.config import SiteConfig
from app.layout import site_layout

SESSION_KEY = "is_admin"
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300.0


class LoginAttemptLimiter:
    """Tracks failed /admin/login attempts per client IP in memory, so a
    client is locked out for LOGIN_LOCKOUT_SECONDS after too many wrong
    passwords in a row. Resets to zero on a correct password. State is
    per-process (lost on restart) — acceptable since restarts only happen
    on deploy, not something an attacker controls."""

    def __init__(
        self,
        max_attempts: int = MAX_FAILED_LOGIN_ATTEMPTS,
        lockout_seconds: float = LOGIN_LOCKOUT_SECONDS,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._max_attempts = max_attempts
        self._lockout_seconds = lockout_seconds
        self._clock = clock
        self._failure_times: dict[str, list[float]] = defaultdict(list)

    def _prune(self, client_ip: str) -> None:
        cutoff = self._clock() - self._lockout_seconds
        self._failure_times[client_ip] = [
            attempt_time
            for attempt_time in self._failure_times[client_ip]
            if attempt_time > cutoff
        ]

    def is_locked_out(self, client_ip: str) -> bool:
        self._prune(client_ip)
        return len(self._failure_times[client_ip]) >= self._max_attempts

    def record_failure(self, client_ip: str) -> None:
        self._failure_times[client_ip].append(self._clock())

    def record_success(self, client_ip: str) -> None:
        self._failure_times.pop(client_ip, None)


login_attempt_limiter = LoginAttemptLimiter()


def verify_password(candidate: str) -> bool:
    expected = SiteConfig().admin_password
    if not expected:
        return False
    return compare_digest(candidate, expected)


def is_authenticated(session) -> bool:
    return bool(session.get(SESSION_KEY))


def require_admin(session) -> Fast.Redirect | None:
    if not is_authenticated(session):
        return Fast.Redirect("/admin/login")
    return None


def admin_nav() -> Fast.Div:
    """A small bar of admin-only controls (back to dashboard, log out),
    shared across every /admin/* page."""
    return Fast.Div(
        Fast.A("Admin", href="/admin"),
        Fast.Form(
            Fast.Button("Log out", type="submit"),
            method="post",
            action="/admin/logout",
        ),
        cls="admin-nav",
    )


def admin_layout(title: str, *content) -> tuple:
    """The shared page shell for authenticated /admin/* pages — always
    includes admin_nav(), so a new admin route can't render without it
    by omission the way a bare content helper could."""
    return site_layout(title, admin_nav(), *content)
