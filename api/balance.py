"""GET /api/vendo/balance — current Vendo credit balance for this deployment.

Thin wrapper over ``vendo.billing.balance()``. Returns 503 when not running
behind Vendo (no VENDO_DEPLOYMENT_ID env), 502 if the SDK fetch fails.
"""
from __future__ import annotations

import json
from typing import Any

import vendo


def handle_balance(handler: Any) -> None:
    """Handle GET /api/vendo/balance. Mounted from api/routes.py."""
    if not vendo.deployment.is_running_on_vendo():
        _json(handler, {"error": "not_running_on_vendo"}, status=503)
        return

    try:
        bal = vendo.billing.balance()
    except Exception as exc:
        _json(handler, {"error": "fetch_failed", "detail": str(exc)}, status=502)
        return

    # Frontend (static/js/vendo-chip.js, static/panels.js) reads
    # ``balance_usd`` — keep that shape; convert micros to USD here.
    _json(
        handler,
        {"balance_usd": bal.credits_remaining_micros / 1_000_000},
        status=200,
    )


def _json(handler, body: dict, *, status: int = 200) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(body).encode())
