from importlib import import_module

from pytest import MonkeyPatch

from conftest import _drop_app_modules


def test_app_uses_session_secret_env_var_as_signing_key(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SESSION_SECRET", "a-fixed-test-secret")
    _drop_app_modules()
    try:
        main_module = import_module("app.main")
        assert main_module.app.secret_key == "a-fixed-test-secret"
    finally:
        _drop_app_modules()
