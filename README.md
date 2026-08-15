# Terrace

A single-user tool for building comparisons out of Premier League data covering
1992/93 to the present, and sharing the result as a link with a rich preview.

Terrace exists for two reasons: quick access to the numbers that settle
arguments between supporters, and evidence of reproducible data work. The core
data model carries no Premier League specifics, so adding a competition is a
configuration change plus a source adapter, never a schema change.

Read `SPEC.md` for the full design. Read `CLAUDE.md` for how the work is done
and the constraints that hold it in shape.

## Layout

```
pipeline/       Python ingest, dbt project, registries
  ingest/       one module per source, deterministic parsers only
  dbt/          staging -> core -> marts
  registry/     metrics.yml, clubs.yml, people.yml, aliases.*.yml
  data/         dated raw snapshots and the local build database
web/            Next.js App Router application
notebooks/      composite metric development, not part of the build
docs/           SPEC companions, data sources, decisions, metric definitions
scripts/        CI gates and automation
.claude/        agent configuration, hooks, rules, skills
.github/        workflows, CODEOWNERS, pull request templates
```

## Commands

```
make ingest      # fetch raw source data to pipeline/data/raw
make build       # dbt build, runs all tests
make check       # quality gates, lint, typecheck
make publish     # write Parquet artefacts to web/public/data
make dev         # run the web app locally
make help        # list the targets
```

The Python side is managed by `uv`. The web application is built on
`@hannasage/projection-ui` and queried in the browser by DuckDB-WASM over static
Parquet, so there is no backend and no query endpoint.

## Data

Every source is recorded in `docs/DATA-SOURCES.md` with a terms status, and a
source without an entry fails the build. Missing data renders as a gap, never as
an interpolated or zero-filled value. Observed and constructed metrics are
labelled distinctly everywhere they appear. See `docs/DECISIONS.md` for the
record of material decisions.

## Status

Early scaffold. The repository skeleton, quality gates, and build tooling are in
place. Ingest, the dbt project, the metric registry, and the web application are
not yet implemented. See `BOOTSTRAP.md` for the remaining setup steps.
