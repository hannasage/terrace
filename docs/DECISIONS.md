# DECISIONS.md

Newest first. Each entry is self-contained. Decisions are superseded by new
entries, never edited away.

Format: ID, date, decision, evidence, what it rules out.

---

## D-016 (2026-08-26): The hosted MCP requires an API key in a request header

**Decision.** The hosted MCP server requires an API key on every HTTP request,
carried in a header (`Authorization: Bearer <key>` or `X-API-Key: <key>`) and
checked in constant time against `TERRACE_API_KEY`. A request without a valid key
is refused with 401. The endpoint is a plain `/mcp`; the connector is registered
with authentication None and the key supplied through its request-headers field.
The server is served with `uvicorn.run` rather than the SDK's `run()`.

**Evidence.** The connector's Add dialog exposes a request-headers field for an
API key, so Claude sends a real credential on every call. That is stronger than
D-015's unguessable path, which was obscurity carried in the URL, and it is the
familiar API-key model. A pure-ASGI middleware wraps the SDK's Starlette app to
enforce it; it must be pure ASGI, not Starlette's BaseHTTPMiddleware, which
buffers the body and would break the MCP server-sent-event streaming. The 401
carries no WWW-Authenticate challenge, so Claude does not attempt OAuth. Serving
with `uvicorn.run` also fixes a shutdown fault: the previous `server.run` path
called `anyio.run`, which raised a KeyboardInterrupt traceback whenever Fly sent
SIGINT; uvicorn installs its own signal handlers and exits cleanly.

**Supersedes.** D-015's secret-path mechanism. The intent is unchanged and now met
properly: the endpoint is private, exposing only read-only query tools, reachable
only with the key. Removes the secret-path logic and the `TERRACE_MCP_TOKEN` and
`TERRACE_PUBLIC_URL` variables.

**Rules out.** A gate that lives in the URL rather than a verified credential, and
running the HTTP server through `server.run` where SIGINT is not handled cleanly.

---

## D-015 (2026-08-26): The hosted MCP is a public server gated by an unguessable path

**Decision.** The hosted MCP server advertises no OAuth and is reached as a public
custom connector. The gate is the URL path: the server mounts at `/<secret>/mcp`,
where the secret is `TERRACE_MCP_TOKEN`, so the address is unguessable. There is
no bearer-token check on requests.

**Evidence.** D-014 assumed a bearer token would gate the endpoint. Claude's
custom-connector flow does not support that: it always attempts OAuth dynamic
client registration, and a server that advertises OAuth without fully implementing
an authorization server fails with "couldn't register with the sign-in service",
which is exactly what happened. Anthropic's own guidance is that a server which
advertises no OAuth (its `.well-known` endpoints return 404) is connected as a
public server. So the realistic choices are a full OAuth authorization server,
which is heavy for a single personal user, or a public server. A public server
gated by a secret path is chosen: it is the same strength as a bearer token
carried in the URL, and the exposure is read-only tools over already-public
Premier League facts, so the stakes are low. The SDK bug where the auth code also
prevented the container from binding its port is removed by dropping the auth
path entirely.

**Supersedes.** The bearer-token mechanism of D-014. D-014's intent holds: the
endpoint is private in practice (unguessable, unadvertised, personal) and exposes
only the read-only query tools. Removes `mcp_server/auth.py` and its test.

**Rules out.** A bearer-token check against Claude's connector, since the platform
does not send one. Full OAuth stays available in the SDK if a future need or a
non-public data source ever justifies it.

---

## D-014 (2026-08-25): A private, authenticated remote MCP endpoint for multi-device access

**Decision.** The Terrace MCP server is additionally hosted as a small public
HTTPS endpoint, gated by a bearer token, and registered as a custom connector so
Claude can reach it from any device, the mobile app included. The local stdio
server for Claude Desktop and Claude Code is unchanged and stays the default; the
hosted instance is an additional deployment of the same code, serving the same
verified data.

**Evidence.** The Desktop tools already produce verified answers with a rendered
chart. Bringing that to mobile is a reach problem, not a visualisation one: Claude
connects to a remote MCP server from Anthropic's cloud, not from the device, so a
device-reachable server must be a public HTTPS endpoint. Verified against the
Anthropic connector docs, August 2026: custom remote-MCP connectors work on the
mobile app on the Max plan, and the server must be reachable from Anthropic's IP
ranges. The `mcp` SDK already serves HTTP and carries first-class bearer and OAuth
auth, so no new dependency is needed. The endpoint is authenticated and reachable
only with Hanna's token, and every tool is read-only over already-public Premier
League facts, so it is personal use consistent with D-003, not the public data
service operating principle 3 forbids.

**Supersedes.** The absolute "no hosting" reading of D-013. D-013's substance
holds: no hosted web product, no DuckDB-WASM, no share links, and the local Claude
apps stay the primary interface. What changes is that the tool layer may also be
reached remotely, privately, so it is not confined to one machine.

**Rules out.** An unauthenticated or public endpoint, any write tool, and hosting
the web product that D-013 dropped. The remote server exposes only the read-only
query tools, behind a token.

---

## D-013 (2026-08-25): The interface is Claude apps over local MCP tools, not a hosted site

**Decision.** Terrace drops the hosted web product and delivers its interface
through Claude's apps instead. The deterministic pipeline stays: ingest, dbt
transforms, the quality gates, the registry, and the GitHub automation are all
kept. On top of the verified data sits a local MCP server exposing deterministic
query tools, and the user interface is Claude Desktop and Claude Code driving a
team of agents that produce reports on demand. Natural language in, a verified
report out. The model orchestrates and narrates; the coded tools compute.

Four layers, each consuming the one below: ingest, transform, a local MCP tool
layer, and a Claude-app UX. The model lives only in the top layer, so run-time
determinism and fail-closed behaviour are unchanged: the tools return gaps as
gaps and label constructed values, and the agents never invent a number.

**Evidence.** Three reasons. Cost: the Claude Max subscription already held
covers the usage, where hosting and API credits would not. UX: for a single
personal user, Claude's apps are a better interface than a self-hosted site.
Focus: the near-term goal is personal daily use, settling supporter arguments,
for which a queryable tool the user already lives in beats a site to visit. The
coded pipeline is what guarantees the reports are accurate and repeatable, so it
is the half that stays; the web surface was the expensive half and the one being
reconsidered.

**Supersedes.** D-006's framing of the front end (DuckDB-WASM in the browser over
static Parquet on a CDN) as the delivery mechanism. The no-backend,
Parquet-plus-DuckDB data model is unchanged; only the client changes, from a
browser app to a local MCP server the Claude apps call. Also supersedes the
Next.js, Vercel, and share-link elements of the SPEC section 5 application design.

**Rules out.** A hosted web application, a public URL, DuckDB-WASM in a browser,
share links, and link-preview image rendering. The MCP tools return data to the
user's own agent for personal use, which is consistent with D-003; they are not
the public export or data service that operating principle 3 forbids.

---

## D-012 (2026-08-16): Club and person registries are split by nation, not league

**Decision.** The canonical club registry is per nation: `clubs.eng.yml` now,
`clubs.<nation>.yml` as other countries are added, and the same shape for
`people.<nation>.yml`. Not per league or per tier. The guardrail hook protects
the `clubs.`, `people.` and `aliases.` prefixes so every per-nation file stays
Hanna's.

**Evidence.** A club moves between leagues within a nation through promotion and
relegation, so a league cannot own a club's canonical id, which D-002 fixes as
competition-agnostic. The 51 English clubs seeded from engsoccerdata have
appeared in the Premier League, but most also spend seasons in lower tiers, and
`england.csv` holds 147 English clubs across all four tiers. Clubs are disjoint
across nations, so a per-nation file has no such overlap. Which competition a
club played in is a fact in the data, captured in `club_season` and marts, not a
property of the filename.

**Supersedes.** The initial per-league naming `clubs.pl.yml`, which would have
forced a relegated club to belong to two files at once.

**Rules out.** Per-league or per-tier registry files, and any club appearing in
more than one registry file within a nation.

---

## D-011 (2026-08-15): The registry-edit guardrail runs in the session, not in CI

**Decision.** `check_registry_not_edited` runs only in the local PreToolUse hook,
which stops Claude from writing `clubs.yml`, `people.yml` and `aliases.*.yml`. It
is removed from `scripts/guardrails_ci.py`, so the CI `guardrails` job no longer
blocks a diff that touches those files.

**Evidence.** The CI check cannot tell who authored an edit. Hanna is the sole
editor of these files, so running the rule in CI blocked the one person allowed
to change them: every registry edit failed the `guardrails` check and needed an
admin override to merge. CODEOWNERS already routes `pipeline/registry/` to
Hanna's approval, so a registry edit reaching a pull request is legitimate by
construction. The local hook still enforces the rule against Claude, where the
concern actually lives.

**Rules out.** Relying on the branch check to keep Claude out of the registry.
That guarantee comes from the session hook plus CODEOWNERS, not from CI.

---

## D-010 (2026-08-15): Ingest is change-gated, with per-source state

**Decision.** Each source keeps a small state file at
`pipeline/data/state/<source>.json` recording its last position: an ETag, a
content hash, and the snapshot path. A refresh compares against that position and
writes a new dated snapshot only when the source has changed. When it has not,
nothing is downloaded, nothing is stored, and no pull request opens. Snapshots
are stored gzip compressed.

**Evidence.** Historic results do not change, so most refreshes have nothing new.
Writing a full 15 MB snapshot on every run would grow the data lane without
adding information. Verified 2026-08-15: `raw.githubusercontent.com` returns a
content ETag and answers `If-None-Match` with a 304 and no body, so an unchanged
engsoccerdata refresh transfers almost nothing. gzip takes the stored snapshot
from roughly 15 MB to roughly 4 MB, and DuckDB reads it directly. The state file
is a mutable pointer, distinct from the immutable snapshots it points at, and is
committed so a fresh CI checkout resumes from the last known position.

**Consequences.** The per-source state is the general mechanism; each adapter
decides what "changed" means for its source. engsoccerdata compares an ETag on a
monolithic file. football-data re-fetches only the current season. Understat
never re-fetches a completed season. The runner stays ignorant of the strategy.

**Rules out.** Re-storing an unchanged source, and any assumption that a snapshot
exists for every scheduled run. A gap between snapshot dates means no change, not
a missed run.

---

## D-009 (2026-08-15): Ingest captures raw bytes, reconciliation lives in dbt

**Decision.** An ingest adapter fetches its source and writes a dated, immutable
snapshot, nothing more. Club-name and person-name resolution, and the
fail-closed behaviour on an unrecognised name, happen in the dbt staging and
core layers, not in the adapter.

**Evidence.** SPEC.md 4.5 places reconciliation in the transformation path,
reading the committed alias registry. Keeping the fetch dumb is what keeps it
deterministic and cheap to reason about: the same URL on the same day yields the
same snapshot, and a snapshot once written is never rewritten. Validating names
at fetch time would couple the network step to the hand-maintained registry and
duplicate logic that dbt already owns.

**Supersedes.** The wording in BOOTSTRAP.md Phase 4, which asked ingest itself to
fail closed on an unknown club name. The fail-closed guarantee is unchanged; it
moves one layer inward, to where the alias registry is read.

**Rules out.** Club or person validation, aliasing, or any registry read inside
pipeline/ingest/. Adapters know sources, not clubs.

---

## D-008 (2026-08-13): Automation metrics recorded per milestone

**Decision.** Each milestone closes with four numbers recorded in this file:
share of pull requests authored end to end by Claude Code, human interventions
per feature and their kind, time from request to deployed, and count of
documented-constraint violations that reached human review.

**Evidence.** The build model is half the point of the project. Without recorded
numbers the experiment produces only anecdote.

**Rules out.** Judging the project solely on the finished application.

---

## D-007 (2026-08-13): Preview images use a separate render path

**Decision.** Link preview images are rendered from a small dedicated component
set with resolved hex values, not from `@hannasage/projection-ui`.

**Evidence.** The image renderer supports a limited CSS subset and silently
ignores CSS custom properties, CSS grid and `calc()`. The component library is
themed entirely through `--ui-*` custom properties. Reuse would render blank or
unstyled without erroring.

**Rules out.** Sharing chart components between the application and the preview
renderer. Accept the duplication; share the palette constants only.

---

## D-006 (2026-08-13): No backend. DuckDB-WASM over static Parquet

**Decision.** Published Parquet files are served statically and queried in the
browser by DuckDB-WASM over HTTP range requests. No API layer, no hosted
database.

**Evidence.** The dataset is small, the access pattern is analytical and
read-only, and range requests fetch only the byte ranges a query needs. Removes
hosting cost, removes a query endpoint to secure, and lets the user compose
arbitrary comparisons without an endpoint per question.

**Consequences.** The WASM bundle is large and must load lazily in a worker with
a usable interface meanwhile. The published Parquet is readable by anyone with
the URL, which the about page states plainly rather than implying otherwise.

**Rules out.** A server-rendered query API, and any design that assumes data can
be withheld from a determined visitor.

---

## D-005 (2026-08-13): Name reconciliation is proposed, approved, then frozen

**Decision.** A model proposes club and person name mappings offline as
structured output constrained to existing canonical ids. Hanna approves. The
approved mapping is committed as an alias file. The pipeline reads only the
committed file. Unknown names fail the build.

**Evidence.** The failure mode of runtime fuzzy matching is two different
players collapsed onto one id, producing a chart that is wrong, plausible, and
shared. Determinism at run time is worth the manual approval step, which is a
few minutes per promotion window.

**Rules out.** Any model call or fuzzy match inside `pipeline/`.

---

## D-004 (2026-08-13): engsoccerdata is the spine, not the primary source

**Decision.** engsoccerdata supplies 1992/93 and acts as an independent
cross-check on results. football-data.co.uk is primary from 1993/94.

**Evidence.** Verified against both the raw CSV and the packaged binary on
2026-08-13. English tier 1 ends at season 2024/25. The whole of 2022/23 is
missing across all four tiers, zero rows, in both artefacts. The schema carries
no match statistics and no player data. A per-season match-count assertion
caught this in under a second.

**Supersedes.** An earlier working assumption that engsoccerdata was current to
the end of 2025/26 and could serve as the MVP primary source.

**Rules out.** Depending on any single source for completeness. Drives the
completeness and agreement gates in `SPEC.md` section 4.6.

---

## D-003 (2026-08-13): Personal tool, unlisted deployment

**Decision.** Single-user analytical tool and portfolio artefact, deployed to an
unlisted subdomain. No promotion, no accounts, no commercial element. Share
links work for anyone holding the URL.

**Evidence.** Personal and research use sits inside what the sources offer.
Publishing a promoted public product would not.

**Rules out.** Advertising, subscriptions, a public API, and any framing of the
project as a service to others.

---

## D-002 (2026-08-13): Competition-agnostic core model

**Decision.** No Premier League specifics in `core`. Adding a competition is a
configuration change plus a source adapter.

**Evidence.** The portfolio audience is second-division clubs in the United
States. The demonstrable claim is that the machinery transfers, which requires
that it actually does.

**Rules out.** Premier League column names, twenty-club assumptions, and
English-calendar assumptions in `core` models.

---

## D-001 (2026-08-13): FBref excluded entirely

**Decision.** No FBref or Stathead data, including for historical backfill.

**Evidence.** Sports Reference's data use page states that websites and tools
should not be built on data scraped from their sites without permission. Second,
on 20 January 2026 they removed all advanced soccer data after their provider
terminated the feed and required deletion, so the advanced statistics are frozen
as well as prohibited.

**Rules out.** The default architecture most published tutorials assume. Drives
the reliance on Understat for expected goals and the fantasy API for player
level.
