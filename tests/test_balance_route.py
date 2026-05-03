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

    import vendo
    from vendo.billing import Balance
    fake_balance = Balance(
        credits_remaining_micros=12_340_000,
        currency="USD",
        top_up_url="",
    )
    fake_billing = mock.MagicMock()
    fake_billing.balance.return_value = fake_balance
    monkeypatch.setattr(vendo, "billing", fake_billing)

    h = _mock_handler()
    balance_route.handle_balance(h)

    h.send_response.assert_called_with(200)
    written = h.wfile.write.call_args[0][0]
    body = json.loads(written.decode())
    assert body == {"balance_usd": 12.34}
    assert isinstance(body["balance_usd"], (int, float))


def test_returns_502_on_sdk_failure(monkeypatch):
    monkeypatch.setenv("VENDO_DEPLOYMENT_ID", "dep_abc")
    import vendo
    fake_billing = mock.MagicMock()
    fake_billing.balance.side_effect = RuntimeError("boom")
    monkeypatch.setattr(vendo, "billing", fake_billing)

    h = _mock_handler()
    balance_route.handle_balance(h)
    h.send_response.assert_called_with(502)
