# SPEC.md

Terrace. A personal analytical tool for exploring Premier League data and
composing custom comparisons.

Status: draft v0.1, 13 Aug 2026. Not approved. Author: Hanna Sage.

> Name is a placeholder. Change it here first, then everywhere else.

---

## 1. What this is

A single-user tool for building comparisons out of Premier League data covering
1992/93 to the present, and sharing the result as a link with a rich preview.

It exists for two reasons, and both shape the design:

1. **Use.** Quick access to the numbers that settle arguments between supporters.
2. **Portfolio.** Evidence of the skills a second-division club would hire for:
   reproducible ingestion, tested transformations, documented data quality,
   deterministic reconciliation, and a working front end over the result.

The second reason has a design consequence that is easy to miss. A club like
Loudoun United FC in the USL Championship does not care about the Premier
League. They care whether the same machinery could be pointed at their data. So
the core data model carries no Premier League specifics, and adding a
competition is a configuration change plus a source adapter, never a schema
change. Premier League is the first competition loaded, not the only one the
system can hold.

## 2. What this is not

- Not a public product. No ads, no accounts, no subscriptions, no marketing.
- Not a data service. No public API, no CSV or JSON export, no bulk endpoint.
- Not a live-score app. Data refreshes on a schedule, never in real time.
- Not a prediction or betting tool. No forecasts, no odds, no model outputs
  presented as expectations about future matches.
- Not multi-league at MVP, though the model must not prevent it.

## 3. Operating principles

These are constraints, not aspirations. Where a principle can be enforced by a
hook or a test rather than by intent, it is, and the enforcement is named.

1. **No source is used against its published terms.** Every source carries a
   recorded status in `docs/DATA-SOURCES.md`: cleared, tolerated, or excluded.
   Adding a source without a register entry fails the build.
2. **Non-commercial.** No advertising, payment, sponsorship, or affiliate link
   anywhere in the application.
3. **No redistribution.** The product presents data. It does not hand it back
   out. No export route, no download button, no public query endpoint.
   Enforced by hook.
4. **Attribution is visible.** Each view names the sources behind the numbers
   on screen, not in a buried footer.
5. **Missing data is a finding.** Gaps render as explicit gaps. No
   interpolation, no estimation, no zero standing in for absent. Enforced by
   test at the mart layer.
6. **Observed and constructed stay separated.** Every metric declares which it
   is. Constructed metrics carry a definition link everywhere they appear,
   including in shared previews.
7. **Facts are verified before they are embedded.** Anything entering a fixed
   string in the codebase (club founding years, ground names, competition
   formats) is checked against a source and cited in the commit.
8. **Composites are defined elsewhere.** A composite metric enters the pipeline
   only after it has been built, tested, and reviewed in a notebook. The
   pipeline computes an approved definition. It does not invent one.
9. **Determinism at run time.** No model call, no network fetch, and no fuzzy
   match inside the transformation path. Same inputs produce the same outputs.
10. **Fail closed.** Unrecognised club names, unmapped players, unexpected row
    counts and missing seasons stop the run. They do not warn and continue.

## 4. Data

### 4.1 Sources and roles

Full detail in `docs/DATA-SOURCES.md`. Summary:

| Source | Role | Range | Cadence |
|---|---|---|---|
| engsoccerdata | Historical spine, sole source for 1992/93 | 1888 to 2024/25 | Sporadic |
| football-data.co.uk | Primary results and match statistics | 1993/94 onward | Twice weekly |
| Understat | Team and player xG, shot level | 2014/15 onward | Live |
| FPL API | Player level per gameweek | 2016/17 onward | Live |
| ClubElo | Club strength series | Deep history | Daily |

engsoccerdata is a spine and a cross-check, not the primary source. Verified
2026-08-13: its England file ends at season 2024/25 and is missing the whole of
2022/23 across all four tiers, in both the packaged binary and the raw CSV. See
`docs/DECISIONS.md` D-004.

### 4.2 Capability tiers

Metric availability steps up over the covered period. The application must know
these boundaries and surface them, because a comparison that crosses one is
comparing a number against nothing.

| From | Adds |
|---|---|
| 1992/93 | Results, from engsoccerdata only |
| 1993/94 | Results, two independent sources |
| 1995/96 | Half-time state |
| 2000/01 | Shots, shots on target, fouls, corners, cards, referee |
| 2014/15 | Team and player xG, npxG, xGChain, xGBuildup, PPDA |
| 2016/17 | Player level per gameweek |
| 2022/23 | Player xG and xA in the fantasy feed |
| 2025/26 | Player defensive contribution counts |

Every metric in the registry declares `available_from`. The comparison builder
reads it and refuses to plot a metric outside its range, showing the gap instead.

### 4.3 Core model

Grain is fixed and competition-agnostic.

```
competition   one row per competition
season        one row per competition-season
club          one row per club, stable id across renames
person        one row per player or staff member
match         one row per match
appearance    one row per person per match
club_season   one row per club per season
person_season one row per person per season
```

Nothing in `core` may reference the Premier League by name. Competition-specific
logic lives in `marts`.

### 4.4 Metric registry

The single most important artefact in the repo. Every number the application can
plot is declared once, in `pipeline/registry/metrics.yml`, with:

```yaml
- id: npxg_per_90
  label: Non-penalty xG per 90
  grain: person_season
  unit: per_90
  kind: constructed          # observed | constructed
  available_from: "2014-15"
  sources: [understat]
  definition_url: docs/metrics/npxg_per_90.md
  higher_is_better: true
  precision: 2
```

The comparison builder, the axis pickers, the share encoder and the OG renderer
all read the registry. None of them contains a hardcoded metric list. Adding a
metric means adding a registry entry, a dbt model and a test, and nothing else.

This is what makes the product open-ended rather than a fixed set of dashboards.
The two questions that started this project ("who has improved this decade",
"who are the difference-makers") are example prompts, not features.

### 4.5 Reconciliation

Club and person names diverge across sources. Resolution is deterministic:

1. A hand-maintained canonical list lives in `pipeline/registry/clubs.yml` and
   `pipeline/registry/people.yml`. Only Hanna edits these.
2. When a source emits an unrecognised name, the build fails with the offending
   value and the source it came from.
3. Resolving it is an offline task. A batch job asks a model to propose mappings
   as structured output constrained to the existing canonical ids, with evidence
   and a confidence value. It may not invent an id.
4. Hanna approves or rejects each proposal. Approved mappings are written to
   `pipeline/registry/aliases.<source>.yml` and committed.
5. The pipeline reads only the committed alias files. The model is never in the
   run path.

The failure this defends against: two different players collapsed onto one id,
producing a chart that is wrong, plausible, and shared.

### 4.6 Quality gates

Run on every build, failing rather than warning:

- **Completeness.** Expected match count per competition-season. 462 for
  Premier League 1992/93 to 1994/95, 380 from 1995/96. No gaps in a continuous
  season range. Every club appears exactly 2(n-1) times per season.
- **Agreement.** Where two sources cover the same match, scorelines must match.
  Disagreements are listed, not averaged.
- **Referential integrity.** Every appearance resolves to a person and a match.
  Every match resolves to two clubs and a season.
- **Registry coverage.** Every mart column maps to a registry entry. Every
  registry entry maps to a mart column.
- **Tier honesty.** No metric emits a non-null value before its
  `available_from`.

## 5. Application

Reframed by `docs/DECISIONS.md` D-013. The application is no longer a hosted web
app with Explore, Compare, and Share screens. It is Claude's apps calling a local
MCP tool layer. The surfaces below describe capabilities the tools and agents
provide, not web pages. Ask, once a later phase, is now the primary paradigm.

### 5.1 Surfaces

**Explore.** Ask about a competition, season, club, or match and get a
registry-driven summary. The tools read the registry, so there is no bespoke
logic per club.

**Compare.** The core capability. Name two or more entities of the same grain, a
metric from the registry, and a season range; a tool returns the aligned series
and an agent renders the report. Filtered to the grain by the registry.

**Share.** A report is a Claude artefact or a saved file, not a public URL. No
link unfurling, no preview image rendering (D-013 rules these out).

**Ask.** The primary paradigm now, not a later phase. Natural language in, a
verified report out, via the agent team over the tools. See 5.4.

### 5.2 Stack

Superseded in part by `docs/DECISIONS.md` D-013. The pipeline rows below are
current. The interface is no longer a hosted web app: the front end, query, and
hosting rows are replaced by a local MCP server and Claude's apps.

| Layer | Choice |
|---|---|
| Ingest | Python, deterministic parsers, one module per source |
| Storage | Parquet artefacts, DuckDB as the local engine |
| Transform | dbt-core with dbt-duckdb, staging then core then marts |
| Orchestration | GitHub Actions on a schedule |
| Tool layer | Local Python MCP server exposing deterministic query tools |
| Interface | Claude Desktop and Claude Code, a team of agents producing reports |

The tool layer carries the design. Verified Parquet is written locally by the
publish step and queried by a local MCP server using DuckDB. The server exposes
registry-driven tools (list the metrics, list the clubs, get a metric, compare
entities) that the Claude apps call. There is no backend to host, no query
endpoint to secure, and no server cost. The model sits above the tools: it
orchestrates and narrates, the tools compute, so run-time determinism holds.

Two constraints that follow from that choice and must be respected:

- The tools are registry-driven, never hardcoded. A metric appears to the agent
  because it is in `metrics.yml`, not because a tool names it.
- A tool returns a gap as an explicit gap and labels a constructed value as
  constructed, so a report built from the tools cannot silently present an
  absent or derived number as an observed one. This is principle 5 and 6 carried
  into the tool layer.

### 5.3 Share links and previews

Comparison state encodes into the URL as readable parameters, not an opaque
blob, so a link is self-describing and survives a schema change with a clear
error rather than a silent misread.

Preview images are generated per comparison at request time. The renderer cannot
reuse `projection-ui` components directly: the image renderer supports a limited
subset of CSS and ignores CSS custom properties, which is the entire theming
mechanism of the component library. So the preview template is a separate,
deliberately small set of components with resolved hex values, sharing the
palette constants but not the components. Budget for this rather than
discovering it late.

Every preview carries the source attribution and, for constructed metrics, the
word that says so.

### 5.4 Ask, phase 2

Text in, comparison specification out. The model returns JSON constrained to the
registry: entity ids, metric ids, season range, chart form. The application
validates that object against the registry and renders it through the same code
path as a manually built comparison. The model never sees a data value and never
produces a number.

When the request is answerable in principle but not with the data held, the
response explains the gap. It does not return an empty chart.

Deferred until Compare and Share are solid, because it is a convenience layer
over a thing that must work without it.

## 6. Milestones

Reframed by `docs/DECISIONS.md` D-013. M0 and M1 are unchanged. The interface
milestones are now delivered through the MCP tools and Claude's apps, not web
pages.

| ID | Deliverable | Done when |
|---|---|---|
| M0 | Spine | Every Premier League season 1992/93 to present loaded, all quality gates green, two sources reconciled |
| M1 | Registry and marts | Metric registry populated for team-level metrics, marts built, tier honesty enforced |
| M2 | Tools | MCP server exposing registry-driven query tools over the published marts |
| M3 | Reports | Agent-produced comparison reports across entities, metrics and seasons |
| M4 | (dropped) | Share links and preview images removed by D-013 |
| M5 | Players | Person grain loaded, reconciled, and exposed to the tools |
| M6 | Ask | Natural language to a verified report, the primary paradigm |

M0 through M2 are the critical path: a verified pipeline with quality gates,
reachable through a coded tool layer, is the foundation everything else builds
on. A trustworthy tool over verified data beats a rich narration over an
unverified one.

## 7. Success criteria

**Product.** A comparison that would take fifteen minutes across three websites
takes under a minute, and the resulting link renders correctly when pasted.

**Data.** Every published number traces to a source and a transformation. Every
gap is visible as a gap. Quality gates run on every build and have caught at
least one real error.

**Automation.** Recorded per milestone in `docs/DECISIONS.md`:

- Share of merged pull requests authored end to end by Claude Code
- Human interventions per feature, and what kind
- Time from request to deployed
- Count of documented-constraint violations that reached review, and whether
  each was preventable by a hook

That last number is the interesting one. A constraint that keeps needing human
catching belongs in a hook, not in prose.

## 8. Open questions

- Does football-data.co.uk publish terms permitting third-party publication?
  Not yet read directly. Affects the register status, not the MVP.
- engsoccerdata licence interaction between the R package licence and the data
  shipped inside it. Needs a read before the dependency is structural.
- Size of the club-name divergence between the two result sources. Unmeasured.
- Whether `projection-ui` renders correctly under server-side rendering, and
  whether `DataTable` virtualises. Needs a build, not a search.
- Which components this project needs that `projection-ui` lacks: scatter with
  quadrants, radar, bump chart, sparkline, combobox, tabs, badge. Each is a
  candidate for upstream contribution before local implementation.
