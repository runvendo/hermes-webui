"""GET /api/connections — list Vendo connections for this deployment.

Thin wrapper over ``vendo.connections.list()``. Returns 503 when not
running behind Vendo (no VENDO_DEPLOYMENT_ID env), 502 if the SDK fetch
fails.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

import vendo

from api import messaging_status


def handle_connections(handler: Any) -> None:
    """Handle GET /api/connections. Mounted from api/routes.py."""
    if not vendo.deployment.is_running_on_vendo():
        _json(handler, {"error": "not_running_on_vendo"}, status=503)
        return

    try:
        items = vendo.connections.list()
    except Exception as exc:
        _json(handler, {"error": "fetch_failed", "detail": str(exc)}, status=502)
        return

    # Feed messaging-gateway-restart hint state. The frontend polls
    # /api/connections, so this is the natural place to record per-poll
    # connection transitions.
    messaging_status.record_poll(items)

    payload = {"connections": [asdict(c) for c in items]}
    _json(handler, payload, status=200)


def handle_messaging_gateway_status(handler: Any) -> None:
    """Handle GET /api/messaging/gateway-status.

    Returns the slugs that have transitioned to ``connected`` since this
    WebUI process started. Those are the messaging connections the sibling
    ``hermes gateway`` process almost certainly hasn't picked up yet (it
    reads bot tokens from env once at startup), so the UI can render a
    "restart the gateway" hint on the affected integration cards.

    Always returns 200 with a stable shape, even when not running on Vendo
    or when no polling has happened yet — the frontend treats an empty
    ``stale_in_gateway`` as "no warning needed".
    """
    payload = messaging_status.get_status()
    _json(handler, payload, status=200)


def _json(handler, body: dict, *, status: int = 200) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(body).encode())
