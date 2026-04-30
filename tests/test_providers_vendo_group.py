import pytest
pytestmark = pytest.mark.no_server


def test_all_three_ai_providers_present_even_without_bindings(monkeypatch):
    """Vendo group should always include openrouter, openai, anthropic."""
    monkeypatch.setattr("api.providers._managed_slugs_now", lambda: frozenset())
    from api.providers import get_providers
    data = get_providers()
    pids = {p["id"] for p in data["providers"]}
    assert {"openrouter", "openai", "anthropic"}.issubset(pids)


def test_unconnected_ai_marked_vendo_available(monkeypatch):
    monkeypatch.setattr("api.providers._managed_slugs_now", lambda: frozenset())
    from api.providers import get_providers
    data = get_providers()
    anthropic = next(p for p in data["providers"] if p["id"] == "anthropic")
    assert anthropic["managed_by"] == "vendo_available"
    assert anthropic["has_key"] is False


def test_connected_ai_marked_vendo_with_has_key_true(monkeypatch):
    monkeypatch.setattr("api.providers._managed_slugs_now", lambda: frozenset({"anthropic"}))
    from api.providers import get_providers
    data = get_providers()
    anthropic = next(p for p in data["providers"] if p["id"] == "anthropic")
    assert anthropic["managed_by"] == "vendo"
    assert anthropic["has_key"] is True
    assert anthropic["base_url"] == "https://anthropic-proxy.vendo.run"
