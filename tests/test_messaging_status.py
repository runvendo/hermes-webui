"""Tests for api.messaging_status and the /api/messaging/gateway-status route.

Covers the transition logic that powers the "restart the Hermes gateway"
warning on freshly-connected messaging integration cards. The sibling
`hermes gateway` process only reads bot tokens at startup, so any
messaging-category slug that transitions empty → connected after webui
boot is flagged here.
"""
import json
from dataclasses import dataclass
from unittest import mock

import pytest

pytestmark = pytest.mark.no_server


@dataclass
class FakeConn:
    slug: str
    status: str = "connected"


@pytest.fixture(autouse=True)
def _reset_messaging_status():
    from api import messaging_status
    messaging_status._reset_for_tests()
    yield
    messaging_status._reset_for_tests()


def test_first_poll_seeds_baseline_no_stale():
    """Connections present at boot are assumed loaded by the gateway."""
    from api import messaging_status

    messaging_status.record_poll([FakeConn(slug="telegram")])
    status = messaging_status.get_status()

    assert status["first_poll_done"] is True
    assert status["stale_in_gateway"] == []


def test_new_messaging_connection_after_boot_is_stale():
    """A messaging slug that appears on a later poll counts as stale."""
    from api import messaging_status

    # First poll: nothing connected
    messaging_status.record_poll([])
    # Second poll: telegram appears
    messaging_status.record_poll([FakeConn(slug="telegram")])
    status = messaging_status.get_status()

    assert status["stale_in_gateway"] == ["telegram"]


def test_disconnect_clears_stale_for_slug():
    """If the user disconnects a messaging slug, drop its stale flag."""
    from api import messaging_status

    messaging_status.record_poll([])  # baseline empty
    messaging_status.record_poll([FakeConn(slug="slack")])  # becomes stale
    assert "slack" in messaging_status.get_status()["stale_in_gateway"]

    messaging_status.record_poll([])  # disconnected
    assert messaging_status.get_status()["stale_in_gateway"] == []


def test_non_messaging_slugs_ignored():
    """AI providers (openai, anthropic) shouldn't trigger gateway warnings."""
    from api import messaging_status

    messaging_status.record_poll([])  # baseline
    messaging_status.record_poll([
        FakeConn(slug="openai"),
        FakeConn(slug="anthropic"),
        FakeConn(slug="notion"),
    ])
    assert messaging_status.get_status()["stale_in_gateway"] == []


def test_pending_status_does_not_count_as_connected():
    """A connection in `pending` or `error` state doesn't mark gateway stale."""
    from api import messaging_status

    messaging_status.record_poll([])  # baseline
    messaging_status.record_poll([FakeConn(slug="telegram", status="pending")])
    assert messaging_status.get_status()["stale_in_gateway"] == []

    messaging_status.record_poll([FakeConn(slug="telegram", status="error")])
    assert messaging_status.get_status()["stale_in_gateway"] == []


def test_transition_only_fires_on_add_not_every_poll():
    """Polling repeatedly with the same connected slug doesn't duplicate it."""
    from api import messaging_status

    messaging_status.record_poll([])  # baseline
    messaging_status.record_poll([FakeConn(slug="telegram")])
    messaging_status.record_poll([FakeConn(slug="telegram")])
    messaging_status.record_poll([FakeConn(slug="telegram")])
    assert messaging_status.get_status()["stale_in_gateway"] == ["telegram"]


def test_route_returns_payload():
    """GET /api/messaging/gateway-status returns the current snapshot."""
    from api import connections as connections_route, messaging_status

    messaging_status.record_poll([])  # baseline
    messaging_status.record_poll([FakeConn(slug="discord")])

    h = mock.MagicMock()
    h.headers = {}
    h.wfile = mock.MagicMock()
    connections_route.handle_messaging_gateway_status(h)

    h.send_response.assert_called_with(200)
    body = json.loads(h.wfile.write.call_args[0][0].decode())
    assert body["stale_in_gateway"] == ["discord"]
    assert body["first_poll_done"] is True
    assert isinstance(body["process_started_at"], (int, float))


def test_route_works_without_running_on_vendo():
    """Endpoint returns 200 even when not on Vendo — UI just sees empty list."""
    from api import connections as connections_route

    h = mock.MagicMock()
    h.headers = {}
    h.wfile = mock.MagicMock()
    connections_route.handle_messaging_gateway_status(h)

    h.send_response.assert_called_with(200)
    body = json.loads(h.wfile.write.call_args[0][0].decode())
    assert body["stale_in_gateway"] == []


def test_pre_turn_records_messaging_transitions(monkeypatch):
    """The streaming pre-hook calls messaging_status.record_poll each turn."""
    import os as _os
    from unittest.mock import MagicMock
    from api.streaming_vendo_hook import vendo_pre_turn
    import api.streaming_vendo_hook as hook
    from api import messaging_status

    @dataclass
    class HookConn:
        slug: str
        status: str = "connected"
        display_name: str = ""
        fields: dict = None

        def __post_init__(self):
            if self.fields is None:
                self.fields = {}

    hook._PREV_SLUGS = frozenset()

    seq = [
        [],  # baseline: nothing
        [HookConn(slug="telegram", fields={"bot_token": "abc"})],  # new connection
    ]
    monkeypatch.setattr(hook, "_sdk_refresh", MagicMock())
    monkeypatch.setattr(hook, "_sdk_list", MagicMock(side_effect=seq))
    monkeypatch.setattr(_os, "environ", {})

    vendo_pre_turn()
    assert messaging_status.get_status()["stale_in_gateway"] == []

    vendo_pre_turn()
    assert messaging_status.get_status()["stale_in_gateway"] == ["telegram"]
