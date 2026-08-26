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
- `head_to_head(club_a, club_b, season_from?, season_to?)` : every league meeting
  between two clubs, with each club's record. The fixture level view.
- `club_matches(club, season)` : one club's fixtures in one season, oldest first.
- `report_style(theme?)` : the house report format, a JSX skeleton to copy, and
  the resolved theme tokens. Called before building a report artifact.
- `list_themes()` : every report theme with its core colours and contrast facts.

The metrics are club-season grain, so they hold how a season ended rather than
who won a given match. `head_to_head` and `club_matches` read the match grain and
are what answer a "who beats whom" question.

The tools are registry-driven: a metric exists because it is in
`pipeline/registry/metrics.yml`, never because a tool names it. A season a club
did not play, or a season before a metric exists, comes back as an explicit gap,
never a zero. The tools read the committed Parquet in `pipeline/data/published/`,
so make sure it is current (`make publish`) after a data change.

## Prompts

- `analysis_mode(mode)` : set the reading level mid conversation.
- `terrace_report(question)` : answer a question as a full styled report artifact.

## How answers are shaped

The server sends instructions to every client in the MCP initialize result, so
they apply on Desktop, on the web, and through the hosted connector alike. They
are built in `guidance.py` and cover three things.

**Reading level.** One of three, resolved before the first substantive answer:

| Mode | Reader | Prose |
|---|---|---|
| `learning` | a high school statistics student | defines terms, explains the relationship, says what to look at next |
| `exploration` | a college statistician in training | assumes the vocabulary, puts the follow up question back to you rather than answering it |
| `analytics` | a working analyst | answers what was asked and stops |

If you state your level, it is used. Otherwise `TERRACE_DEFAULT_MODE` is used if
set, and if it is not, the agent asks once and holds the answer for the
conversation. An unrecognised value stops the server rather than being ignored.

**Prose economy.** Prose is for teaching and guidance, so its budget comes from
the reading level. It never restates what a chart already shows and never narrates
a number you can read. In `analytics` the report is the artifact and the chat
reply is a line or two.

Because a client is free to ignore an MCP server's instructions, and one did on
the first hosted test, the same contract also rides on every tool result as a
`presentation` block and is repeated in the tool descriptions. Those two channels
are not optional: the model cannot answer without reading them.

**Reports.** Anything beyond a single figure goes in an artifact. `report_style`
returns the format contract from `style/CONTRACT.md`, the skeleton from
`style/template.jsx`, and the theme tokens. Set `TERRACE_STYLE_FILE` to a Markdown
file of your own to replace the contract; a style defined in your own project
context wins over the server default in any case.

## Themes

A report ships with two themes, one dark and one light, swapped by a selector in
the artifact. The defaults are `projection` and `coastal-day`. The rest are opt
in: name one and it replaces the slot matching its own mode, so asking for a light
theme keeps the default dark one beside it.

```
Dark    projection, midnight-reef, neon-arcade, deep-forest,
        ember-tide, noir-bloom, dusk-protocol, pillow-fort
Light   coastal-day, fernwood, dust-and-flame, confetti-studio
```

The palettes are vendored verbatim from `app/lib/projection-themes.ts` in the
`hannasage/resume` repository, never invented here. Re-vendor them when that file
changes:

```
uv run python scripts/vendor_themes.py ../resume/app/lib/projection-themes.ts
```

`list_themes` reports WCAG contrast per theme, computed rather than eyeballed.
Text and muted clear the floor everywhere. Accent does not: in `fernwood` and
`dust-and-flame` it sits below 4.5:1 against its own background, so
`accent_safe_for_text` is false there and the contract tells the agent to keep
words out of it and use it for graphics only.

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
device, so to use Terrace from the mobile app the server runs as a small HTTPS
endpoint registered as a custom connector. This is recorded in `docs/DECISIONS.md`
D-014 and D-016. The local stdio server above is unchanged and stays the default;
this is an additional deployment of the same code.

Claude's custom-connector flow supports OAuth or a plain endpoint with a
credential header. Terrace advertises no OAuth and requires an API key on every
request: `Authorization: Bearer <key>` (or `X-API-Key: <key>`), checked against
`TERRACE_API_KEY`. Run it locally to check the gate:

```
TERRACE_TRANSPORT=streamable-http TERRACE_API_KEY=<a secret> \
  uv run python mcp_server/server.py
# the endpoint is http://localhost:8000/mcp; a request without the key gets 401
```

### Deploy to Fly.io

From the repository root, so the build context includes the bundled data:

```
fly apps create --generate-name          # or: fly apps create <unique-name>
fly secrets set TERRACE_API_KEY=<a long random string> -a <app-name>
fly deploy -a <app-name> --config mcp_server/fly.toml --dockerfile mcp_server/Dockerfile
```

Pass `-a <app-name>` explicitly so the deploy always knows the app. The image
bundles `pipeline/data/published/` and `pipeline/registry/metrics.yml`, so the
host serves the data as of the last deploy. Redeploy after a data refresh to serve
fresher numbers.

### Register the connector

In Claude settings, add a custom connector:

- URL: `https://<app-name>.fly.dev/mcp`
- Authentication: None (the server advertises no OAuth)
- Request header: `Authorization` = `Bearer <your TERRACE_API_KEY>`

Terrace's tools then appear on Desktop, web, and the mobile app. A request without
the header, or with a wrong key, is refused with 401.

### Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `TERRACE_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `TERRACE_API_KEY` | shared secret required on every HTTP request | none (required for HTTP) |
| `TERRACE_HTTP_HOST` | bind address for HTTP | `0.0.0.0` |
| `TERRACE_HTTP_PORT` | port for HTTP | `8000` (`8080` in the image) |
| `TERRACE_DATA_DIR` | directory holding the published Parquet | the repo's `pipeline/data/published/` |
| `TERRACE_METRICS` | path to `metrics.yml` | the repo's `pipeline/registry/metrics.yml` |
| `TERRACE_DEFAULT_MODE` | pinned reading level: `learning`, `exploration` or `analytics` | none (the agent asks once) |
| `TERRACE_STYLE_FILE` | your own Markdown format contract, replacing the default | none (the built-in contract) |

## Layout

- `server.py` : the MCP wrapper. Declares the tools and the guidance the agent
  needs to use them honestly, and chooses the transport from the environment.
- `terrace_tools.py` : the deterministic query functions. Tested by
  `test_terrace_tools.py`, so the logic is verified without the MCP transport.
- `guidance.py` : the instructions every client receives. Tested by
  `test_guidance.py`.
- `style_tools.py` : the format contract, the theme registry and the contrast
  arithmetic. Tested by `test_style_tools.py`.
- `style/` : `CONTRACT.md` the house format, `template.jsx` the skeleton to copy,
  `themes.json` the vendored palettes.
- `api_key_auth.py` : the pure-ASGI API-key gate for the hosted HTTP server.
  Tested by `test_api_key_auth.py`.
- `Dockerfile`, `fly.toml` : the lean image and Fly.io config for the hosted
  connector.
