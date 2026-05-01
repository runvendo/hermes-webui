"""Track messaging-category connection transitions for gateway-restart hints.

The hermes gateway (a sibling process — `hermes gateway run`) reads
TELEGRAM_BOT_TOKEN / SLACK_BOT_TOKEN / etc. from its environment **once at
startup**. When a user connects Telegram or Slack via Vendo *after* the
gateway is already running, ``api.vendo_env.hydrate()`` will set the env var
in the WebUI process — but the gateway's own environment is unchanged, so
no messages flow until the gateway is restarted.

This module records messaging-category slugs that transitioned to
``status='connected'`` after the WebUI process started. Those are the slugs
the gateway almost certainly hasn't picked up yet, and the UI can surface
that fact via ``GET /api/messaging/gateway-status``.

Intentionally additive: we never restart the user's gateway, we just tell
them when one is needed.
"""
from __future__ import annotations

import threading
import time
from typing import Iterable

# Messaging-category slugs hermes-agent gateway adapters care about.
# Kept in sync with hermes-agent gateway/platforms/* and hermes-webui's
# vendo_catalog. Treat anything in this set as "needs gateway restart"
# when freshly connected.
MESSAGING_SLUGS: frozenset[str] = frozenset({
    "telegram",
    "slack",
    "discord",
    "whatsapp",
    "messenger",
})

# Process-start timestamp. Recorded at module import (which happens during
# server boot, before any connection poll). Connections seen as "connected"
# on the first poll are assumed to predate this process AND its sibling
# gateway, so they do NOT count as "needs restart".
_PROCESS_STARTED_AT: float = time.time()

_LOCK = threading.Lock()
_FIRST_POLL_DONE: bool = False
# Messaging slugs known to be connected *before* the WebUI's first poll.
# Treated as "the gateway already has these tokens" (best-effort heuristic).
_CONNECTED_AT_BOOT: set[str] = set()
# Messaging slugs that have transitioned empty→connected since boot.
# These are the slugs the gateway almost certainly hasn't loaded yet.
_STALE_IN_GATEWAY: set[str] = set()


def record_poll(connections: Iterable) -> None:
    """Update transition state from the latest connection list.

    Called from ``api.streaming_vendo_hook.vendo_pre_turn`` once per turn,
    after the SDK refresh. The first call seeds ``_CONNECTED_AT_BOOT`` with
    whatever's currently connected; subsequent calls diff against the prior
    snapshot and add any newly-connected messaging slugs to the stale set.

    Idempotent and side-effect-free beyond updating module state.
    """
    global _FIRST_POLL_DONE
    connected_messaging: set[str] = set()
    for conn in connections:
        slug = getattr(conn, "slug", None)
        status = getattr(conn, "status", None)
        if slug in MESSAGING_SLUGS and status == "connected":
            connected_messaging.add(slug)

    with _LOCK:
        if not _FIRST_POLL_DONE:
            _CONNECTED_AT_BOOT.update(connected_messaging)
            _FIRST_POLL_DONE = True
            return
        # Subsequent polls: any slug now connected that wasn't connected at
        # boot is new and the gateway hasn't seen it yet.
        for slug in connected_messaging:
            if slug not in _CONNECTED_AT_BOOT:
                _STALE_IN_GATEWAY.add(slug)
        # If a slug disconnects, drop it from the stale set — restarting the
        # gateway no longer matters for that slug.
        for slug in list(_STALE_IN_GATEWAY):
            if slug not in connected_messaging:
                _STALE_IN_GATEWAY.discard(slug)


def get_status() -> dict:
    """Return the current messaging gateway status snapshot.

    Shape:
        {
          "process_started_at": <unix seconds>,
          "first_poll_done": bool,
          "stale_in_gateway": ["telegram", ...],   # connected after boot
        }
    """
    with _LOCK:
        return {
            "process_started_at": _PROCESS_STARTED_AT,
            "first_poll_done": _FIRST_POLL_DONE,
            "stale_in_gateway": sorted(_STALE_IN_GATEWAY),
        }


def _reset_for_tests() -> None:
    """Test-only hook to clear module state between cases."""
    global _FIRST_POLL_DONE
    with _LOCK:
        _FIRST_POLL_DONE = False
        _CONNECTED_AT_BOOT.clear()
        _STALE_IN_GATEWAY.clear()
