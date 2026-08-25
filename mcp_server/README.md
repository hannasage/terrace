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

## Reach it from mobile: a hosted connector

Claude connects to a remote MCP server from Anthropic's cloud, not from your
device, so to use Terrace from the mobile app the server runs as a small public
HTTPS endpoint, gated by a bearer token, registered as a custom connector. This is
recorded in `docs/DECISIONS.md` D-014. The local stdio server above is unchanged
and stays the default; this is an additional deployment of the same code.

The server switches to HTTP when `TERRACE_TRANSPORT=streamable-http`, and then
requires `Authorization: Bearer <TERRACE_MCP_TOKEN>` on every request. Run it
locally that way to check the gate:

```
TERRACE_TRANSPORT=streamable-http TERRACE_MCP_TOKEN=<secret> \
  uv run python mcp_server/server.py
```

### Deploy to Fly.io

From the repository root, so the build context includes the bundled data:

```
fly launch --config mcp_server/fly.toml --dockerfile mcp_server/Dockerfile --no-deploy
fly secrets set TERRACE_MCP_TOKEN=<a long random string>
fly secrets set TERRACE_PUBLIC_URL=https://<app-name>.fly.dev
fly deploy --config mcp_server/fly.toml --dockerfile mcp_server/Dockerfile
```

The image bundles `pipeline/data/published/` and `pipeline/registry/metrics.yml`,
so the host serves the data as of the last deploy. Redeploy after a data refresh
to serve fresher numbers.

### Register the connector

In Claude settings, add a custom connector pointing at `https://<app-name>.fly.dev/mcp`
with the bearer token. Terrace's tools then appear on Desktop, web, and the mobile
app. If the connector flow asks for OAuth rather than a bearer token, the SDK also
supports a full OAuth provider; swap `StaticTokenVerifier` for it in `auth.py`.

### Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `TERRACE_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `TERRACE_MCP_TOKEN` | bearer secret required for HTTP | none (required for HTTP) |
| `TERRACE_PUBLIC_URL` | the server's own public URL | `http://localhost:<port>` |
| `TERRACE_HTTP_HOST` | bind address for HTTP | `0.0.0.0` |
| `TERRACE_HTTP_PORT` | port for HTTP | `8000` (`8080` in the image) |
| `TERRACE_DATA_DIR` | directory holding the published Parquet | the repo's `pipeline/data/published/` |
| `TERRACE_METRICS` | path to `metrics.yml` | the repo's `pipeline/registry/metrics.yml` |

## Layout

- `server.py` : the MCP wrapper. Declares the tools and the guidance the agent
  needs to use them honestly, and chooses the transport from the environment.
- `terrace_tools.py` : the deterministic query functions. Tested by
  `test_terrace_tools.py`, so the logic is verified without the MCP transport.
- `auth.py` : the bearer-token verifier for the hosted HTTP server. Tested by
  `test_auth.py`.
- `Dockerfile`, `fly.toml` : the lean image and Fly.io config for the hosted
  connector.
