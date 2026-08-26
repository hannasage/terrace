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
# Claude's custom-connector flow supports OAuth or a plain endpoint with a
# credential header, not a native bearer scheme it negotiates. The hosted server
# advertises no OAuth and requires an API key on every request, supplied through
# the connector's request-headers field. The key is checked by ApiKeyMiddleware.
# See docs/DECISIONS.md D-016.
TRANSPORT = os.environ.get("TERRACE_TRANSPORT", "stdio")
HTTP_HOST = os.environ.get("TERRACE_HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.environ.get("TERRACE_HTTP_PORT", "8000"))

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
        import uvicorn

        from api_key_auth import ApiKeyMiddleware

        api_key = os.environ.get("TERRACE_API_KEY", "")
        if not api_key:
            raise SystemExit(
                "TERRACE_API_KEY must be set to a secret when serving over HTTP."
            )
        # Build the same Starlette app run() would, then wrap it with the API-key
        # gate before uvicorn serves it. transport_security stays at the default
        # that the plain run() path uses and that works behind the Fly proxy.
        app = server.streamable_http_app(streamable_http_path="/mcp", host=HTTP_HOST)
        app.add_middleware(ApiKeyMiddleware, api_key=api_key)
        uvicorn.run(app, host=HTTP_HOST, port=HTTP_PORT)
    else:
        server.run(transport="stdio")
