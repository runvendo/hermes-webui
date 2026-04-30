"""GET /api/connections — list Vendo connections for this deployment.

Thin wrapper over vendo_sdk.connections. Returns 503 when not running
behind Vendo (no VENDO_DEPLOYMENT_ID env), 502 if the SDK fetch fails.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from vendo_sdk import connections as vendo_connections
from vendo_sdk.deployment import is_running_on_vendo


def handle_connections(handler: Any) -> None:
    """Handle GET /api/connections. Mounted from api/routes.py."""
    if not is_running_on_vendo():
        _json(handler, {"error": "not_running_on_vendo"}, status=503)
        return

    try:
        items = vendo_connections.list()
    except Exception as exc:
        _json(handler, {"error": "fetch_failed", "detail": str(exc)}, status=502)
        return

    payload = {"connections": [asdict(c) for c in items]}
    _json(handler, payload, status=200)


def _json(handler, body: dict, *, status: int = 200) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(body).encode())
