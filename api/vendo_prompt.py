"""Build the Vendo connections block prepended to the agent's system prompt.

Branches per `refresh_kind` (catalog-driven):

- **static**: credentials are stable (Telegram bot tokens, Notion workspace
  tokens, Vendo-managed AI proxy keys). Env-var hydration works; saved
  skills can reference $VAR_NAME directly.
- **refreshing**: short-lived OAuth access tokens (Gmail, Slack, MS, etc.).
  Env vars are captured at turn start and may expire mid-turn or by the
  time a saved skill replays. The agent must call vendo_sdk.session(slug)
  or vendo_sdk.token(slug) at point-of-use — see vendo-sdk-py v0.4.
"""
from __future__ import annotations

from typing import Iterable, Protocol

from api import vendo_catalog
from api.vendo_env import _conn_fields


class _ConnectionLike(Protocol):
    """Tolerant duck-type for SDK Connection across versions; see
    api.vendo_env._conn_fields for the field-flattening contract."""
    slug: str
    display_name: str


def _refresh_kind(slug: str) -> str:
    """Return the catalog's refresh_kind for slug, defaulting to 'static'."""
    meta = vendo_catalog.lookup(slug) or {}
    return meta.get("refresh_kind") or "static"


def _format_static_line(conn, meta: dict) -> list[str]:
    """Render a per-field bullet for a static connection."""
    native_map = meta.get("native_env_map", {})
    docs_url = meta.get("docs_url")
    out: list[str] = []
    for field_name in _conn_fields(conn).keys():
        ns = f"VENDO_CONN_{conn.slug.upper()}_{field_name.upper()}"
        native = native_map.get(field_name)
        env_str = f"${native} (also ${ns})" if native else f"${ns}"
        line = f"- {conn.slug} → {field_name} in {env_str}."
        if docs_url:
            line += f" Docs: {docs_url}"
        out.append(line)
    return out


def _format_refreshing_line(conn, meta: dict) -> str:
    """Render a single bullet for a refreshing (OAuth) connection."""
    docs_url = meta.get("docs_url")
    line = (
        f"- {conn.slug} → "
        f'vendo_sdk.session("{conn.slug}") for HTTP, '
        f'vendo_sdk.token("{conn.slug}") for the raw token.'
    )
    if docs_url:
        line += f" Docs: {docs_url}"
    return line


def build_block(connections: Iterable[_ConnectionLike]) -> str:
    conns = list(connections)
    if not conns:
        return ""

    static_pairs: list[tuple[object, dict]] = []
    refreshing_pairs: list[tuple[object, dict]] = []
    for c in conns:
        meta = vendo_catalog.lookup(c.slug) or {}
        if (meta.get("refresh_kind") or "static") == "refreshing":
            refreshing_pairs.append((c, meta))
        else:
            static_pairs.append((c, meta))

    lines = ["## Vendo connections (live)", ""]
    lines.append("These services are connected via Vendo and ready to use.")
    if static_pairs:
        lines.append("Their credentials are already in your environment.")
    lines.append("")

    if static_pairs:
        lines.append("Connected:" if not refreshing_pairs else "Static (credentials in your environment):")
        for conn, meta in static_pairs:
            lines.extend(_format_static_line(conn, meta))
        lines.append("")

    if refreshing_pairs:
        lines.append("Refreshing (tokens expire and rotate — use the SDK):")
        for conn, meta in refreshing_pairs:
            lines.append(_format_refreshing_line(conn, meta))
        lines.append("")

    lines.append("Behavior:")
    lines.append(
        "- On first successful use of any of these, save a skill so future calls are fast and reliable."
    )
    if refreshing_pairs:
        lines.append(
            "- For refreshing connections: access tokens expire mid-session and rotate. "
            "Always call vendo_sdk.session(slug) or vendo_sdk.token(slug) at point-of-use "
            "inside saved skills — never embed a literal access token or read "
            "$..._ACCESS_TOKEN, since both will be stale by the next replay."
        )
    lines.append(
        "- If the user asks for an integration that is not in this list, "
        "point them to https://vendo.run/connections to connect it."
    )
    return "\n".join(lines)
