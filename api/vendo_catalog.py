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
    # 'static' (default when missing) — credentials are stable; env-var
    #   hydration is fine and saved skills may reference $VAR_NAME directly.
    # 'refreshing' — short-lived OAuth access tokens that expire mid-turn
    #   or between skill replays (Gmail, Slack, MS, etc.). Saved skills
    #   must call vendo_sdk.session(slug) or vendo_sdk.token(slug) at
    #   point-of-use rather than reading $..._ACCESS_TOKEN.
    refresh_kind: str


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
    # AI providers — native_env_map ensures hydrate() sets the standard
    # provider env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) plus
    # base URLs pointing at the Vendo proxy. Without this the agent's
    # OpenAI/Anthropic clients fall back to api.openai.com / api.anthropic.com
    # and use whatever stale OPENAI_API_KEY happens to be set, bypassing
    # Vendo's billing + auth entirely.
    "anthropic": {
        "kind": "ai",
        "native_env_map": {
            "api_key": "ANTHROPIC_API_KEY",
            "base_url": "ANTHROPIC_BASE_URL",
        },
        "proxy_url": "https://anthropic-proxy.vendo.run",
        "docs_url": "https://docs.anthropic.com",
    },
    "openai": {
        "kind": "ai",
        "native_env_map": {
            "api_key": "OPENAI_API_KEY",
            "base_url": "OPENAI_BASE_URL",
        },
        # MUST include /v1 — the OpenAI Python SDK appends "/chat/completions"
        # straight to base_url. Without /v1 the request hits an unknown route
        # and the proxy 404s ("route_not_supported").
        "proxy_url": "https://openai-proxy.vendo.run/v1",
        "docs_url": "https://platform.openai.com/docs",
    },
    "openrouter": {
        "kind": "ai",
        # OpenRouter is OpenAI-compatible; hermes routes it via the same
        # OPENAI_* env vars when active_provider="openrouter". When both
        # openrouter and openai are bound, last-wins on these vars — but
        # hermes' resolve_model_provider() uses the provider-prefixed
        # model id (e.g. "anthropic/claude-opus-4.6") so the active
        # provider still picks the right base_url at request time.
        "native_env_map": {
            "api_key": "OPENROUTER_API_KEY",
            "base_url": "OPENROUTER_BASE_URL",
        },
        # MUST include /api/v1 — OpenRouter sits under /api/v1, NOT /v1 like
        # OpenAI. Without it the proxy returns 200 + the OpenRouter web app's
        # HTML homepage, which the OpenAI SDK silently parses as an empty
        # completion (root cause of the picker's "(empty)" reply bug).
        "proxy_url": "https://openrouter-proxy.vendo.run/api/v1",
        "docs_url": "https://openrouter.ai/docs",
    },
}

AI_SLUGS = frozenset({s for s, m in _CATALOG.items() if m.get("kind") == "ai"})


def lookup(slug: str) -> Optional[IntegrationMeta]:
    """Return catalog metadata for a slug, or None if unknown."""
    return _CATALOG.get(slug)
