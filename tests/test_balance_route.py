import json
from unittest import mock

from api import balance as balance_route


def _mock_handler():
    """Create a fake handler matching BaseHTTPRequestHandler interface."""
    h = mock.MagicMock()
    h.headers = {}
    h.wfile = mock.MagicMock()
    return h


def test_returns_503_when_not_running_on_vendo(monkeypatch):
    monkeypatch.delenv("VENDO_DEPLOYMENT_ID", raising=False)
    h = _mock_handler()
    balance_route.handle_balance(h)
    h.send_response.assert_called_with(503)


def test_returns_balance_payload_when_running_on_vendo(monkeypatch):
    monkeypatch.setenv("VENDO_DEPLOYMENT_ID", "dep_abc")

    fake_body = {"balance_usd": 12.34, "tenant_id": "t_xyz"}
    with mock.patch("vendo_sdk.client.get", return_value=fake_body):
        h = _mock_handler()
        balance_route.handle_balance(h)

    h.send_response.assert_called_with(200)
    written = h.wfile.write.call_args[0][0]
    body = json.loads(written.decode())
    assert body == {"balance_usd": 12.34}
    assert isinstance(body["balance_usd"], (int, float))


def test_returns_502_on_sdk_failure(monkeypatch):
    monkeypatch.setenv("VENDO_DEPLOYMENT_ID", "dep_abc")
    with mock.patch("vendo_sdk.client.get", side_effect=RuntimeError("boom")):
        h = _mock_handler()
        balance_route.handle_balance(h)
    h.send_response.assert_called_with(502)
