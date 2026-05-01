"""GET /api/vendo/balance — current Vendo credit balance for this deployment.

Thin wrapper over vendo_sdk.client. Returns 503 when not running behind
Vendo (no VENDO_DEPLOYMENT_ID env), 502 if the SDK fetch fails.
"""
from __future__ import annotations

import json
from typing import Any

from vendo_sdk import client as vendo_client
from vendo_sdk.deployment import is_running_on_vendo


def handle_balance(handler: Any) -> None:
    """Handle GET /api/vendo/balance. Mounted from api/routes.py."""
    if not is_running_on_vendo():
        _json(handler, {"error": "not_running_on_vendo"}, status=503)
        return

    try:
        body = vendo_client.get("/api/v1/balance")
    except Exception as exc:
        _json(handler, {"error": "fetch_failed", "detail": str(exc)}, status=502)
        return

    # Drop tenant_id; the front end only needs the balance.
    _json(handler, {"balance_usd": body.get("balance_usd")}, status=200)


def _json(handler, body: dict, *, status: int = 200) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(body).encode())
