import json
from unittest import mock
import pytest

from api import connections as connections_route


def _mock_handler():
    """Create a fake handler matching BaseHTTPRequestHandler interface."""
    h = mock.MagicMock()
    h.headers = {}
    h.wfile = mock.MagicMock()
    return h


def test_returns_503_when_not_running_on_vendo(monkeypatch):
    monkeypatch.delenv("VENDO_DEPLOYMENT_ID", raising=False)
    h = _mock_handler()
    connections_route.handle_connections(h)
    h.send_response.assert_called_with(503)


def test_returns_connections_payload_when_running_on_vendo(monkeypatch):
    monkeypatch.setenv("VENDO_DEPLOYMENT_ID", "dep_abc")

    # Build a real Connection dataclass (don't fake it — the SDK serializer
    # uses asdict, so the test needs a real frozen dataclass instance).
    from vendo_sdk.connections import Connection
    fake_conn = Connection(
        slug="openrouter", display_name="OpenRouter", category="ai",
        profile="vendo_managed_pool", status="connected",
        api_key="vendo_sk_x", base_url="https://openrouter-proxy.vendo.run/api/v1",
        metadata={}, setup_url=None, error_message=None,
    )

    with mock.patch("vendo.connections.list", return_value=[fake_conn]):
        h = _mock_handler()
        connections_route.handle_connections(h)

    h.send_response.assert_called_with(200)
    written = h.wfile.write.call_args[0][0]
    body = json.loads(written.decode())
    assert body["connections"][0]["slug"] == "openrouter"
    assert body["connections"][0]["api_key"] == "vendo_sk_x"


def test_returns_502_on_sdk_failure(monkeypatch):
    monkeypatch.setenv("VENDO_DEPLOYMENT_ID", "dep_abc")
    with mock.patch("vendo.connections.list", side_effect=RuntimeError("boom")):
        h = _mock_handler()
        connections_route.handle_connections(h)
    h.send_response.assert_called_with(502)
