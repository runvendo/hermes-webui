"""Overlay hermes_cli's runtime provider resolver with Vendo proxy config.

When a user's selected AI provider (anthropic/openai/openrouter) is
connected via Vendo, swap the api_key + base_url for Vendo's proxy.
Otherwise, fall through to upstream behavior.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from api import vendo_catalog

logger = logging.getLogger(__name__)


def _connected_slugs() -> frozenset[str]:
    """Indirection for tests — defaults to the SDK live state."""
    try:
        from vendo_sdk import connections as _conn
        return frozenset(_conn.connected_slugs())
    except Exception:
        logger.debug("vendo_sdk.connections.connected_slugs() unavailable", exc_info=True)
        return frozenset()


def _upstream_resolver(name: str):
    """Indirection for tests — defaults to hermes_cli's resolver."""
    try:
        from hermes_cli.runtime_provider import resolve_runtime_provider
        return resolve_runtime_provider(name)
    except Exception:
        logger.debug("hermes_cli.runtime_provider unavailable", exc_info=True)
        return None


def resolve_runtime_provider_with_vendo(name: str) -> Optional[dict]:
    """Drop-in replacement for hermes_cli.runtime_provider.resolve_runtime_provider.

    If `name` is an AI slug connected via Vendo, return Vendo proxy config.
    Otherwise, return whatever upstream returns.
    """
    upstream = _upstream_resolver(name)

    if name not in vendo_catalog.AI_SLUGS:
        return upstream

    if name not in _connected_slugs():
        return upstream

    meta = vendo_catalog.lookup(name) or {}
    proxy_url = meta.get("proxy_url")
    api_key = os.environ.get("VENDO_API_KEY")

    if not proxy_url or not api_key:
        logger.warning(
            "vendo overlay skipped for %s: proxy_url=%s api_key_set=%s",
            name, bool(proxy_url), bool(api_key),
        )
        return upstream

    overlaid = dict(upstream or {})
    overlaid["api_key"] = api_key
    overlaid["base_url"] = proxy_url
    return overlaid
