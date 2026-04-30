import pytest
pytestmark = pytest.mark.no_server

from api.vendo_overlay import resolve_runtime_provider_with_vendo


def _stub_resolver(name):
    if name == "anthropic":
        return {"api_key": "sk-user-anthropic", "base_url": "https://api.anthropic.com"}
    return None


def test_passthrough_when_slug_not_connected(monkeypatch):
    monkeypatch.setattr("api.vendo_overlay._connected_slugs", lambda: frozenset())
    monkeypatch.setattr("api.vendo_overlay._upstream_resolver", _stub_resolver)
    out = resolve_runtime_provider_with_vendo("anthropic")
    assert out["api_key"] == "sk-user-anthropic"


def test_overlays_when_slug_connected(monkeypatch):
    monkeypatch.setattr("api.vendo_overlay._connected_slugs", lambda: frozenset({"anthropic"}))
    monkeypatch.setattr("api.vendo_overlay._upstream_resolver", _stub_resolver)
    monkeypatch.setenv("VENDO_API_KEY", "vendo_sk_test")
    out = resolve_runtime_provider_with_vendo("anthropic")
    assert out["api_key"] == "vendo_sk_test"
    assert out["base_url"] == "https://anthropic-proxy.vendo.run"


def test_passthrough_for_non_ai_slug(monkeypatch):
    monkeypatch.setattr("api.vendo_overlay._connected_slugs", lambda: frozenset({"telegram"}))
    monkeypatch.setattr("api.vendo_overlay._upstream_resolver", _stub_resolver)
    out = resolve_runtime_provider_with_vendo("anthropic")
    assert out["api_key"] == "sk-user-anthropic"


def test_returns_none_when_upstream_none_and_not_connected(monkeypatch):
    monkeypatch.setattr("api.vendo_overlay._connected_slugs", lambda: frozenset())
    monkeypatch.setattr("api.vendo_overlay._upstream_resolver", _stub_resolver)
    assert resolve_runtime_provider_with_vendo("nonexistent") is None
