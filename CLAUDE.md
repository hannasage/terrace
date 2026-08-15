# CLAUDE.md

Terrace. Personal Premier League analysis tool. Read `SPEC.md` before proposing
any change to scope, data model, or stack.

Hanna is project lead and reviewer. You are the engineer. Work autonomously
within the constraints below and stop at the checkpoints in "When to stop".

## Layout

```
pipeline/       Python ingest, dbt project, registries
  ingest/       one module per source, deterministic parsers only
  dbt/          staging -> core -> marts
  registry/     metrics.yml, clubs.yml, people.yml, aliases.*.yml
web/            Next.js App Router application
notebooks/      composite metric development, not part of the build
docs/           DATA-SOURCES.md, DECISIONS.md, metrics/
```

## Commands

```
make ingest          # fetch raw source data to pipeline/data/raw
make build           # dbt build, runs all tests
make check           # quality gates, lint, typecheck
make publish         # write Parquet artefacts to web/public/data
make dev             # run the web app locally
```

Run `make check` before proposing any change as complete. A change that has not
passed `make check` is not finished.

## Non-negotiable constraints

Some of these are enforced by hooks in `.claude/hooks/`. A hook blocking you is
the system working, not a bug to route around. If you believe a hook is wrong,
stop and say so rather than restructuring code to slip past it.

1. No export route, download endpoint, or public API of any kind.
2. No advertising, payment, analytics-for-sale, or affiliate code.
3. No new data source without a `docs/DATA-SOURCES.md` entry approved by Hanna.
4. No model API call inside `pipeline/`. Model use is offline tooling only.
5. No fuzzy matching, no interpolation, no filling gaps with zero or a mean.
6. No metric that is not declared in `pipeline/registry/metrics.yml`.
7. No hardcoded metric or club list in `web/`. Read the registry.
8. No competition-specific logic in `pipeline/dbt/models/core/`.

## Conventions

- No em-dashes. Anywhere. Code comments, commit messages, documentation, and
  user-facing strings. Use commas, colons, or separate sentences.
- Facts stated in code or copy get verified against a source first, with the
  source named in the commit message. Do not write a founding year, a ground
  name, or a competition rule from memory.
- Observed and constructed values are labelled distinctly in every surface that
  shows them. Never call a constructed score a measurement.
- Failures are loud. Prefer a build that stops with a clear message over one
  that continues with a default.
- One canonical file per concern. No `_v2`, no `_old`, no commented-out
  alternates left behind.

## When to stop and ask

Stop and wait for Hanna on:

- Any change to a data source, its terms status, or the ingest surface
- Any new metric definition, or a change to an existing one
- Any edit to `pipeline/registry/clubs.yml` or `people.yml`
- Any dependency addition
- Any change to the operating principles in `SPEC.md` section 3
- Any component built locally that `@hannasage/projection-ui` should own

Everything else is yours. Do not ask permission to write tests, refactor within
a module, fix a failing gate, or add documentation.

## Working with the UI package

The application is built on `@hannasage/projection-ui`. Before building any
component locally, check whether the package already has it, and whether a
general version belongs upstream. If it belongs upstream, say so and stop.
Upstream first, local second, never both.

## Decisions

Material decisions go in `docs/DECISIONS.md` as a new numbered entry with the
date, the decision, the evidence, and what it rules out. Do not silently reverse
an existing entry. Add a new one that supersedes it and say which.
