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


def _upstream_resolver(requested):
    """Indirection for tests — defaults to hermes_cli's resolver."""
    try:
        from hermes_cli.runtime_provider import resolve_runtime_provider
        return resolve_runtime_provider(requested=requested)
    except Exception:
        logger.debug("hermes_cli.runtime_provider unavailable", exc_info=True)
        return None


def resolve_runtime_provider_with_vendo(requested) -> Optional[dict]:
    """Drop-in replacement for hermes_cli.runtime_provider.resolve_runtime_provider.

    Matches upstream signature: `requested` is the provider id (or None to
    use the default). When the resolved slug is an AI slug connected via
    Vendo, swap api_key + base_url for Vendo's proxy. Otherwise pass through.
    """
    upstream = _upstream_resolver(requested)

    # The slug we evaluate against the Vendo catalog is the one upstream
    # actually resolved (it may have defaulted from None to the user's
    # active provider). Fall back to `requested` when upstream returned None.
    slug = None
    if isinstance(upstream, dict):
        slug = upstream.get("provider") or requested
    else:
        slug = requested

    if slug not in vendo_catalog.AI_SLUGS:
        return upstream

    if slug not in _connected_slugs():
        return upstream

    meta = vendo_catalog.lookup(slug) or {}
    proxy_url = meta.get("proxy_url")
    api_key = os.environ.get("VENDO_API_KEY")

    if not proxy_url or not api_key:
        logger.warning(
            "vendo overlay skipped for %s: proxy_url=%s api_key_set=%s",
            slug, bool(proxy_url), bool(api_key),
        )
        return upstream

    overlaid = dict(upstream or {})
    overlaid["api_key"] = api_key
    overlaid["base_url"] = proxy_url
    return overlaid
