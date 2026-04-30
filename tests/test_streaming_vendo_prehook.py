import os
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest
pytestmark = pytest.mark.no_server


@dataclass
class FakeConn:
    slug: str
    display_name: str = ""
    fields: dict = field(default_factory=dict)


def test_pre_turn_refreshes_and_hydrates(monkeypatch):
    from api.streaming_vendo_hook import vendo_pre_turn

    fake_conns = [FakeConn(slug="telegram", display_name="Telegram",
                           fields={"bot_token": "abc"})]

    refresh_mock = MagicMock()
    list_mock = MagicMock(return_value=fake_conns)

    monkeypatch.setattr("api.streaming_vendo_hook._sdk_refresh", refresh_mock)
    monkeypatch.setattr("api.streaming_vendo_hook._sdk_list", list_mock)
    monkeypatch.setattr(os, "environ", {})

    state = vendo_pre_turn()

    refresh_mock.assert_called_once()
    list_mock.assert_called_once()
    assert "Vendo connections (live)" in state.prompt_block
    assert os.environ.get("VENDO_CONN_TELEGRAM_BOT_TOKEN") == "abc"


def test_pre_turn_fails_soft_on_sdk_error(monkeypatch):
    from api.streaming_vendo_hook import vendo_pre_turn

    monkeypatch.setattr("api.streaming_vendo_hook._sdk_refresh",
                        MagicMock(side_effect=Exception("network")))
    monkeypatch.setattr("api.streaming_vendo_hook._sdk_list",
                        MagicMock(side_effect=Exception("network")))

    state = vendo_pre_turn()

    assert state.prompt_block == ""
    assert state.connected_slugs == frozenset()
