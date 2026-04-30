from dataclasses import dataclass, field

import pytest
pytestmark = pytest.mark.no_server

from api.vendo_prompt import build_block


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
