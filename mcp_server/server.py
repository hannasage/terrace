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

import style_tools as style  # noqa: E402
import terrace_tools as tools  # noqa: E402
from guidance import MODES, build_instructions  # noqa: E402

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

# The instructions reach every client through the initialize result, so the
# reading level handshake and the prose budget apply over stdio and over the
# hosted connector alike. They are built in guidance.py, kept short there because
# they are sent on every conversation; the long format contract sits behind the
# report_style tool instead.
server = MCPServer("terrace", instructions=build_instructions())


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


@server.tool()
def report_style(theme: str | None = None) -> dict:
    """The house format for a Terrace report artifact. Call before building one.

    Returns the format contract, a JSX skeleton to copy rather than compose, and
    the resolved dark and light theme tokens. Pass theme only when the reader
    names one from list_themes; it replaces the slot matching its own mode.

    The themes carry computed contrast. Read it before assigning a colour a job:
    where accent_safe_for_text is false, that theme's accent must not carry
    words, only graphics.
    """
    return style.report_style(theme)


@server.tool()
def list_themes() -> dict:
    """Every report theme, with its core colours and contrast facts.

    A report ships with two themes, one dark and one light. The rest are opt in.
    Mention that alternatives exist once, briefly, when you first produce a
    report, then let the reader raise it.
    """
    return style.list_themes()


@server.prompt()
def analysis_mode(mode: str) -> str:
    """Set the reading level: learning, exploration or analytics."""
    if mode.strip().lower() not in MODES:
        return (
            f"'{mode}' is not a reading level. Ask me for one of: "
            f"{', '.join(MODES)}."
        )
    return (
        f"Use the {mode.strip().lower()} reading level for the rest of this "
        "conversation, as the Terrace server instructions define it. Confirm in "
        "one short line, then wait for my question."
    )


@server.prompt()
def terrace_report(question: str) -> str:
    """Answer a question as a full styled report artifact."""
    return (
        f"{question}\n\n"
        "Answer this as a Terrace report artifact. Resolve my reading level "
        "first if it is not already settled, then call report_style and follow "
        "the contract it returns. Keep the chat reply to a line or two: the "
        "report is the artifact, not the message."
    )


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
