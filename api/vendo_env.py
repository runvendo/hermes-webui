"""Hydrate os.environ with Vendo connection credentials per turn.

For each connection:
- Always set VENDO_CONN_<SLUG>_<FIELD> (uppercase, namespaced).
- If the catalog has a native env name for that field AND the env var is
  not already set, also set the native name. Never overwrite a value the
  user (or upstream tooling) already set.

Track which native names we set so unhydrate() can clean up only our own
values without touching user-set ones.
"""
from __future__ import annotations

import os
import threading
from typing import Iterable, Protocol

from api import vendo_catalog


class _ConnectionLike(Protocol):
    slug: str
    fields: dict


_LOCK = threading.Lock()
_VENDO_SET_NATIVE: dict[str, str] = {}  # var name -> our value


def _ns_var(slug: str, field: str) -> str:
    return f"VENDO_CONN_{slug.upper()}_{field.upper()}"


def hydrate(connections: Iterable[_ConnectionLike]) -> None:
    """Set env vars for each connection. Idempotent across turns."""
    with _LOCK:
        for conn in connections:
            meta = vendo_catalog.lookup(conn.slug) or {}
            native_map = meta.get("native_env_map", {})
            for field_name, value in (conn.fields or {}).items():
                if not value:
                    continue
                # Always set namespaced
                os.environ[_ns_var(conn.slug, field_name)] = str(value)
                # Set native only if not preset (or if WE set it last)
                native = native_map.get(field_name)
                if native:
                    if native not in os.environ or os.environ[native] == _VENDO_SET_NATIVE.get(native):
                        os.environ[native] = str(value)
                        _VENDO_SET_NATIVE[native] = str(value)


def unhydrate(slugs: Iterable[str]) -> None:
    """Remove env vars for slugs that disconnected this turn."""
    with _LOCK:
        for slug in slugs:
            meta = vendo_catalog.lookup(slug) or {}
            native_map = meta.get("native_env_map", {})
            # Remove namespaced — we always own these
            prefix = f"VENDO_CONN_{slug.upper()}_"
            for key in list(os.environ.keys()):
                if key.startswith(prefix):
                    os.environ.pop(key, None)
            # Remove native only if we set it (current value matches our cache)
            for native in native_map.values():
                cached = _VENDO_SET_NATIVE.get(native)
                if cached is not None and os.environ.get(native) == cached:
                    os.environ.pop(native, None)
                _VENDO_SET_NATIVE.pop(native, None)
