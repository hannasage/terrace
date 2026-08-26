"""
Terrace MCP server.

A thin wrapper that exposes the deterministic query tools in terrace_tools.py to
Claude's apps over MCP. Run it over stdio; Claude Desktop and Claude Code launch
it and call the tools. All the logic lives in terrace_tools, so this file only
declares the tool surface and the guidance the agent needs to use it honestly.

    uv run python mcp_server/server.py

See mcp_server/README.md for the Claude Desktop and Claude Code configuration.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer  # noqa: E402

import terrace_tools as tools  # noqa: E402

# Transport is stdio by default, which is what Claude Desktop and Claude Code
# launch as a private subprocess. Set TERRACE_TRANSPORT to streamable-http to
# serve a public HTTPS endpoint for a custom connector.
#
# Claude's custom-connector flow supports only OAuth or a plain public server; it
# has no bearer-token option, and attempting OAuth against a server that does not
# fully implement it fails to register. So the hosted server advertises no OAuth
# and is reached as a public connector. The gate is the path: the server mounts at
# /<secret>/mcp, built from TERRACE_MCP_TOKEN, so the URL is unguessable. That is
# obscurity, not cryptographic auth, which is acceptable here because the tools
# are read-only over already-public Premier League facts. See D-015.
TRANSPORT = os.environ.get("TERRACE_TRANSPORT", "stdio")
HTTP_HOST = os.environ.get("TERRACE_HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.environ.get("TERRACE_HTTP_PORT", "8000"))

_secret = os.environ.get("TERRACE_MCP_TOKEN", "").strip("/")
HTTP_PATH = f"/{_secret}/mcp" if _secret else "/mcp"

server = MCPServer("terrace")


@server.tool()
def list_metrics() -> dict:
    """List every metric that can be queried, from the Terrace registry.

    Each metric carries its kind. Report a value whose kind is "constructed" as
    constructed, never as a measurement, and mention its definition when it
    matters. Call this before answering so the metric ids and their availability
    are known.
    """
    return tools.list_metrics()


@server.tool()
def list_clubs() -> dict:
    """List every canonical Premier League club Terrace holds, with ids."""
    return tools.list_clubs()


@server.tool()
def get_metric(
    club: str,
    metric: str,
    season_from: int | None = None,
    season_to: int | None = None,
) -> dict:
    """One metric's value for one club across a season range.

    club is a club name or id (case-insensitive). metric is an id from
    list_metrics. season_from and season_to are the start years of the range, for
    example 2015 for 2015/16; omit them for the full history. A season the club
    did not play, or a season before the metric exists, comes back with a null
    value and a gap reason. Present the gaps as gaps; never fill them with zero.
    """
    return tools.get_metric(club, metric, season_from, season_to)


@server.tool()
def compare(
    clubs: list[str],
    metric: str,
    season_from: int | None = None,
    season_to: int | None = None,
) -> dict:
    """Compare one metric across two or more clubs over a season range.

    Returns each club's series aligned by season, gaps preserved. Use points per
    game rather than total points when the range crosses the 42-match seasons
    before 1995/96, or includes the in-progress current season, so the comparison
    is fair.
    """
    return tools.compare(clubs, metric, season_from, season_to)


if __name__ == "__main__":
    if TRANSPORT == "streamable-http":
        server.run(
            transport="streamable-http",
            host=HTTP_HOST,
            port=HTTP_PORT,
            streamable_http_path=HTTP_PATH,
        )
    else:
        server.run(transport="stdio")
