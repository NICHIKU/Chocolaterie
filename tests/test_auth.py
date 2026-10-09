import base64

import pytest
from starlette.requests import Request

import app as app_module


def make_request(headers=None):
    """Construit une fausse Request : seule la ligne d'en-tête compte pour is_admin."""
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope)


def basic_auth(user, password):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def fixed_credentials(monkeypatch):
    monkeypatch.setattr(app_module, "ADMIN_USER", "admin")
    monkeypatch.setattr(app_module, "ADMIN_PASSWORD", "delcourt")


def test_is_admin_with_valid_credentials():
    assert app_module.is_admin(make_request(basic_auth("admin", "delcourt"))) is True


def test_is_admin_without_authorization_header():
    assert app_module.is_admin(make_request()) is False


def test_is_admin_with_non_basic_scheme():
    assert app_module.is_admin(make_request({"Authorization": "Bearer token"})) is False
    assert app_module.is_admin(make_request({"Authorization": "Basic"})) is False


def test_is_admin_with_invalid_base64():
    assert app_module.is_admin(make_request({"Authorization": "Basic pas-du-base64!!"})) is False


def test_is_admin_with_wrong_password():
    assert app_module.is_admin(make_request(basic_auth("admin", "mauvais"))) is False


def test_is_admin_with_wrong_user():
    assert app_module.is_admin(make_request(basic_auth("intrus", "delcourt"))) is False


def test_is_admin_with_empty_password():
    assert app_module.is_admin(make_request(basic_auth("admin", ""))) is False


def test_is_admin_with_missing_password_separator():
    token = base64.b64encode(b"admin").decode()
    assert app_module.is_admin(make_request({"Authorization": f"Basic {token}"})) is False
