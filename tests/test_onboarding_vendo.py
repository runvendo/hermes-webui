"""Vendo-aware onboarding tests.

Covers the `vendo` block and step filtering added to /api/onboarding/status when
VENDO_AUTH=1.  Identity comes from request headers (the SSO short-circuit has
already validated them), connections come from the Vendo SDK's cached state.
"""
from unittest import mock

from api import onboarding


def _mock_handler(headers=None):
    h = mock.MagicMock()
    h.headers = headers or {}
    return h


def test_vendo_block_is_active_false_when_VENDO_AUTH_unset(monkeypatch):
    monkeypatch.delenv("VENDO_AUTH", raising=False)
    h = _mock_handler()
    status = onboarding.get_onboarding_status(h)
    assert status["vendo"]["active"] is False


def test_vendo_block_populated_when_VENDO_AUTH_1(monkeypatch):
    monkeypatch.setenv("VENDO_AUTH", "1")
    h = _mock_handler({
        "X-Vendo-User-Id": "u1",
        "X-Vendo-User-Email": "y@vendo.run",
        "X-Vendo-User-Name": "Yousef",
        "X-Vendo-Tenant-Id": "t1",
        "X-Vendo-Role": "owner",
    })
    with mock.patch(
        "vendo_sdk.connections.connected_slugs",
        return_value=frozenset({"openrouter"}),
    ):
        status = onboarding.get_onboarding_status(h)
    assert status["vendo"]["active"] is True
    assert status["vendo"]["identity"]["name"] == "Yousef"
    assert status["vendo"]["identity"]["email"] == "y@vendo.run"
    assert status["vendo"]["connections"]["available"] is True
    assert "openrouter" in status["vendo"]["connections"]["connected_slugs"]
    assert status["vendo"]["connections"]["live_api"] is True


def test_steps_list_under_vendo_auth(monkeypatch):
    monkeypatch.setenv("VENDO_AUTH", "1")
    h = _mock_handler()
    with mock.patch(
        "vendo_sdk.connections.connected_slugs",
        return_value=frozenset(),
    ):
        status = onboarding.get_onboarding_status(h)
    # Setup is split into providers + connections, password is dropped.
    assert status["steps"] == ["system", "providers", "connections", "workspace", "finish"]
    assert "password" not in status["steps"]
    assert "setup" not in status["steps"]


def test_password_step_included_when_VENDO_AUTH_unset(monkeypatch):
    monkeypatch.delenv("VENDO_AUTH", raising=False)
    h = _mock_handler()
    status = onboarding.get_onboarding_status(h)
    assert "password" in status["steps"]


def test_system_check_kind_is_vendo_under_sso(monkeypatch):
    """Agent-import warnings are suppressed under SSO; system_check carries the
    Vendo-flavoured payload instead."""
    monkeypatch.setenv("VENDO_AUTH", "1")
    h = _mock_handler({
        "X-Vendo-User-Id": "u1",
        "X-Vendo-User-Email": "y@vendo.run",
        "X-Vendo-User-Name": "Yousef",
        "X-Vendo-Tenant-Id": "t1",
        "X-Vendo-Role": "owner",
    })
    with mock.patch(
        "vendo_sdk.connections.connected_slugs",
        return_value=frozenset({"openrouter"}),
    ):
        status = onboarding.get_onboarding_status(h)
    assert status["system_check"]["kind"] == "vendo"
    assert status["system_check"]["identity_ok"] is True
    assert status["system_check"]["connections_ok"] is True
    # Missing-modules / import-errors arrays are suppressed.
    assert status["system"]["missing_modules"] == []
    assert status["system"]["import_errors"] == {}


def test_system_check_kind_is_hermes_when_sso_off(monkeypatch):
    monkeypatch.delenv("VENDO_AUTH", raising=False)
    h = _mock_handler()
    status = onboarding.get_onboarding_status(h)
    assert status["system_check"]["kind"] == "hermes"
