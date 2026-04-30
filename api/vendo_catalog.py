"""Fallback metadata for known Vendo connection slugs.

This is a hardcoded backstop so the agent wiring works even if the SDK
hasn't been bumped to v0.3 (which serves the same metadata from the
Vendo backend). Once the v0.3 SDK ships, the SDK is the authoritative
source and this module is consulted only for slugs the SDK hasn't populated.
"""
from __future__ import annotations

from typing import Optional, TypedDict


class IntegrationMeta(TypedDict, total=False):
    kind: str
    native_env_map: dict
    docs_url: str
    proxy_url: str


_CATALOG: dict[str, IntegrationMeta] = {
    "telegram": {
        "kind": "integration",
        "native_env_map": {"bot_token": "TELEGRAM_BOT_TOKEN"},
        "docs_url": "https://core.telegram.org/bots/api",
    },
    "notion": {
        "kind": "integration",
        "native_env_map": {"api_token": "NOTION_TOKEN"},
        "docs_url": "https://developers.notion.com",
    },
    "anthropic": {
        "kind": "ai",
        "proxy_url": "https://anthropic-proxy.vendo.run",
        "docs_url": "https://docs.anthropic.com",
    },
    "openai": {
        "kind": "ai",
        "proxy_url": "https://openai-proxy.vendo.run",
        "docs_url": "https://platform.openai.com/docs",
    },
    "openrouter": {
        "kind": "ai",
        "proxy_url": "https://openrouter-proxy.vendo.run",
        "docs_url": "https://openrouter.ai/docs",
    },
}

AI_SLUGS = frozenset({s for s, m in _CATALOG.items() if m.get("kind") == "ai"})


def lookup(slug: str) -> Optional[IntegrationMeta]:
    """Return catalog metadata for a slug, or None if unknown."""
    return _CATALOG.get(slug)
