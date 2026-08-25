# Terrace MCP server

The local tool layer. A small MCP server that exposes Terrace's verified data to
Claude's apps as deterministic tools, so you can ask a question in plain language
and get a report whose every number traces to the published marts. This is the
interface, in place of a hosted site (see `docs/DECISIONS.md` D-013).

## Tools

- `list_metrics` : every metric that can be queried, with its kind (observed or
  constructed) and the season it becomes available.
- `list_clubs` : every canonical Premier League club Terrace holds.
- `get_metric(club, metric, season_from?, season_to?)` : one metric for one club
  across a season range.
- `compare(clubs, metric, season_from?, season_to?)` : one metric across two or
  more clubs, aligned by season.

The tools are registry-driven: a metric exists because it is in
`pipeline/registry/metrics.yml`, never because a tool names it. A season a club
did not play, or a season before a metric exists, comes back as an explicit gap,
never a zero. The tools read the committed Parquet in `pipeline/data/published/`,
so make sure it is current (`make publish`) after a data change.

## Run it

```
uv run python mcp_server/server.py
```

It speaks MCP over stdio and waits for a client. You will not see output; the
client drives it.

## Connect Claude Desktop

Edit the Claude Desktop config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add Terrace under `mcpServers`, using the absolute path to this repository:

```json
{
  "mcpServers": {
    "terrace": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/hannamacintosh/Projects/Code/terrace",
        "python",
        "mcp_server/server.py"
      ]
    }
  }
}
```

Restart Claude Desktop. Terrace's tools appear in the tools menu. Then ask, for
example: "Compare Arsenal and Tottenham on points per game since 2015, and note
any constructed metrics."

## Connect Claude Code

From the repository root:

```
claude mcp add terrace -- uv run python mcp_server/server.py
```

Claude Code launches the server for the session and can call its tools.

## Layout

- `server.py` : the MCP wrapper. Declares the tools and the guidance the agent
  needs to use them honestly. All logic is delegated.
- `terrace_tools.py` : the deterministic query functions. Tested by
  `test_terrace_tools.py`, so the logic is verified without the MCP transport.
