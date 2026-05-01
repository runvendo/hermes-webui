from dataclasses import dataclass, field

import pytest
pytestmark = pytest.mark.no_server

from api.vendo_prompt import build_block
from api import vendo_catalog


@dataclass
class FakeConn:
    slug: str
    display_name: str = ""
    fields: dict = field(default_factory=dict)


def test_empty_connections_returns_empty_block():
    assert build_block([]) == ""


def test_single_known_integration():
    block = build_block([FakeConn(slug="telegram", display_name="Telegram",
                                  fields={"bot_token": "abc"})])
    assert "Vendo connections (live)" in block
    assert "telegram" in block
    assert "TELEGRAM_BOT_TOKEN" in block
    assert "VENDO_CONN_TELEGRAM_BOT_TOKEN" in block
    assert "https://core.telegram.org/bots/api" in block
    assert "save a skill" in block.lower()


def test_unknown_slug_renders_generically():
    block = build_block([FakeConn(slug="custom_x", fields={"key": "v"})])
    assert "custom_x" in block
    assert "VENDO_CONN_CUSTOM_X_KEY" in block


def test_includes_pointer_to_dashboard():
    block = build_block([FakeConn(slug="telegram", fields={"bot_token": "x"})])
    assert "https://vendo.run/connections" in block


# ─── refresh_kind branching ────────────────────────────────────────────


def test_static_slug_uses_env_var_language():
    """Static slugs (default kind) should keep recommending env-var usage."""
    block = build_block([FakeConn(slug="telegram", fields={"bot_token": "abc"})])
    assert "$TELEGRAM_BOT_TOKEN" in block
    # No SDK guidance leaks into the block when only static slugs are present
    assert "vendo_sdk.session" not in block
    assert "vendo_sdk.token" not in block


def test_refreshing_slug_recommends_sdk_session(monkeypatch):
    """Refreshing slugs must direct the agent to vendo_sdk.session(slug)
    instead of env vars — tokens expire mid-turn / between skill replays."""
    monkeypatch.setitem(
        vendo_catalog._CATALOG,
        "google",
        {
            "kind": "integration",
            "refresh_kind": "refreshing",
            "docs_url": "https://developers.google.com/gmail/api",
        },
    )
    block = build_block([FakeConn(slug="google",
                                  fields={"access_token": "ya29.test"})])
    assert "google" in block
    assert "vendo_sdk.session" in block
    assert "https://developers.google.com/gmail/api" in block
    # Saved-skill discipline guidance — agent must understand why
    assert "expire" in block.lower()


def test_static_and_refreshing_render_separately(monkeypatch):
    """When both kinds are connected, both should appear with the right guidance
    — static keeps env-vars, refreshing uses the SDK."""
    monkeypatch.setitem(
        vendo_catalog._CATALOG,
        "google",
        {
            "kind": "integration",
            "refresh_kind": "refreshing",
            "docs_url": "https://developers.google.com/gmail/api",
        },
    )
    block = build_block([
        FakeConn(slug="telegram", fields={"bot_token": "abc"}),
        FakeConn(slug="google", fields={"access_token": "ya29"}),
    ])
    assert "telegram" in block and "google" in block
    assert "$TELEGRAM_BOT_TOKEN" in block        # static path intact
    assert "vendo_sdk.session" in block          # refreshing path active
