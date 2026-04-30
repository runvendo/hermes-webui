"""Build the Vendo connections block prepended to the agent's system prompt."""
from __future__ import annotations

from typing import Iterable, Protocol

from api import vendo_catalog


class _ConnectionLike(Protocol):
    slug: str
    display_name: str
    fields: dict


def build_block(connections: Iterable[_ConnectionLike]) -> str:
    conns = list(connections)
    if not conns:
        return ""
    lines = ["## Vendo connections (live)", ""]
    lines.append(
        "These services are connected via Vendo and ready to use. "
        "Their credentials are already in your environment."
    )
    lines.append("")
    lines.append("Connected:")
    for conn in conns:
        meta = vendo_catalog.lookup(conn.slug) or {}
        native_map = meta.get("native_env_map", {})
        docs_url = meta.get("docs_url")
        for field_name in (conn.fields or {}).keys():
            ns = f"VENDO_CONN_{conn.slug.upper()}_{field_name.upper()}"
            native = native_map.get(field_name)
            if native:
                env_str = f"${native} (also ${ns})"
            else:
                env_str = f"${ns}"
            line = f"- {conn.slug} → {field_name} in {env_str}."
            if docs_url:
                line += f" Docs: {docs_url}"
            lines.append(line)
    lines.append("")
    lines.append("Behavior:")
    lines.append(
        "- On first successful use of any of these, save a skill so future calls are fast and reliable."
    )
    lines.append(
        "- If the user asks for an integration that is not in this list, "
        "point them to https://vendo.run/connections to connect it."
    )
    return "\n".join(lines)
