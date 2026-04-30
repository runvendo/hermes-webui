"""Per-turn pre-hook that refreshes Vendo state and prepares overlays.

Called by api/streaming.py at the top of every user turn. Returns a
VendoTurnState that the rest of the streaming path reads to install the
prompt block + provider overlay.

Fail-soft: any SDK error returns an empty state. The user's existing
config.yaml + env are unaffected.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

from api import vendo_env, vendo_prompt

logger = logging.getLogger(__name__)

_SDK_FAILURE_LOGGED = False  # log once per process
_PREV_SLUGS: frozenset = frozenset()
_PREV_LOCK = threading.Lock()


def _sdk_refresh():
    from vendo_sdk import connections as _conn
    _conn.refresh()


def _sdk_list():
    from vendo_sdk import connections as _conn
    return list(_conn.list())


@dataclass(frozen=True)
class VendoTurnState:
    prompt_block: str
    connected_slugs: frozenset


def vendo_pre_turn() -> VendoTurnState:
    global _SDK_FAILURE_LOGGED, _PREV_SLUGS
    try:
        _sdk_refresh()
        conns = _sdk_list()
    except Exception:
        if not _SDK_FAILURE_LOGGED:
            logger.warning("vendo_sdk unavailable; skipping connection wiring", exc_info=True)
            _SDK_FAILURE_LOGGED = True
        return VendoTurnState(prompt_block="", connected_slugs=frozenset())

    current_slugs = frozenset(c.slug for c in conns)

    with _PREV_LOCK:
        gone = _PREV_SLUGS - current_slugs
        _PREV_SLUGS = current_slugs

    if gone:
        vendo_env.unhydrate(gone)

    vendo_env.hydrate(conns)
    block = vendo_prompt.build_block(conns)

    return VendoTurnState(prompt_block=block, connected_slugs=current_slugs)
