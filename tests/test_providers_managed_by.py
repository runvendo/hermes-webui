"""Tests for the managed_by field stamped on /api/providers entries."""
from unittest import mock
import json
import pytest

from api import providers as providers_module


def _mock_handler():
    h = mock.MagicMock()
    h.headers = {}
    h.wfile = mock.MagicMock()
    return h


def test_managed_by_stamped_when_slug_in_connected_slugs(monkeypatch):
    """When connected_slugs() includes openrouter, that provider's entry has
    managed_by='vendo'. Other providers have managed_by=None."""
    monkeypatch.setenv("VENDO_DEPLOYMENT_ID", "dep_abc")
    monkeypatch.setenv("OPENROUTER_API_KEY", "vendo_sk_x")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter-proxy.vendo.run/api/v1")

    with mock.patch(
        "vendo_sdk.connections.connected_slugs",
        return_value=frozenset({"openrouter"}),
    ):
        h = _mock_handler()
        providers_module.handle_providers_list(h)

    written = h.wfile.write.call_args[0][0]
    body = json.loads(written.decode())
    by_id = {p["id"]: p for p in body["providers"]}
    assert by_id["openrouter"]["managed_by"] == "vendo"
    if "anthropic" in by_id:
        assert by_id["anthropic"].get("managed_by") in (None, False)


def test_managed_by_none_when_not_running_on_vendo(monkeypatch):
    """When VENDO_DEPLOYMENT_ID is unset, connected_slugs returns empty
    (or raises), so no provider has managed_by='vendo'."""
    monkeypatch.delenv("VENDO_DEPLOYMENT_ID", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-user-byok")

    with mock.patch(
        "vendo_sdk.connections.connected_slugs",
        return_value=frozenset(),
    ):
        h = _mock_handler()
        providers_module.handle_providers_list(h)

    written = h.wfile.write.call_args[0][0]
    body = json.loads(written.decode())
    for p in body["providers"]:
        assert p.get("managed_by") in (None, False)
