---
paths: ["pipeline/**"]
---

# Pipeline rules

The data path is deterministic and fails closed. These rules make SPEC.md
sections 3, 4 executable. The guardrail hook enforces the hard ones; the rest
are reviewed by the `data-quality-reviewer` subagent before a change is proposed
as complete.

## Layering

Three layers, each reading only from the one directly below.

```
staging   one model per raw source, renames and types only, no joins
core      conformed, competition-agnostic entities
marts     competition-specific and metric-bearing models
```

- A `core` model may not name the Premier League, assume twenty clubs, assume a
  38-match season, or assume an English calendar. Competition-specific logic
  lives in `marts`. This is the most common place the rule slips.
- A mart computes from `core`, never from `staging` or raw.
- The core grains are fixed: `competition`, `season`, `club`, `person`, `match`,
  `appearance`, `club_season`, `person_season`. Stable ids survive renames.

## Determinism

Enforced by the hook. Nothing in `pipeline/` may contain:

- A model or network call inside the transformation path.
- Fuzzy matching. Names resolve through the committed alias registry only.
- Interpolation, forward fill, or a zero standing in for an absent value.
- A wall-clock read. The run date is passed in, never read from the clock.

Same inputs produce the same outputs, every run.

## Gaps

Missing data is a finding, not a value to fill. A gap renders as a gap.

- No `COALESCE` that turns a missing measurement into a present one. Most
  `COALESCE` calls are legitimate; some quietly invent data. Check each one.
- Emit `NULL` before a metric's `available_from`, by construction, not by a
  filter bolted on afterward.
- Signs are preserved. A negative goal difference stays negative.

## Reconciliation

Deterministic, per SPEC.md 4.5 and docs/DECISIONS.md D-005.

- Canonical names live in `pipeline/registry/clubs.yml` and `people.yml`. Only
  Hanna edits these. The hook blocks writes to them and to `aliases.*.yml`.
- An unrecognised name from a source fails the build, naming the value and the
  source it came from. Resolving it is an offline task, never a runtime match.
- The pipeline reads only committed alias files.

## The five singular assertions

These live in `pipeline/dbt/tests/` and run as part of `dbt build`. Each is a
spec commitment made executable, and each fails the build rather than warning.

1. `assert_season_match_counts`: expected match count per competition-season.
   462 for Premier League 1992/93 to 1994/95, 380 from 1995/96. No gaps in a
   continuous season range. The known engsoccerdata 2022/23 hole is recorded, so
   that specific absence is expected rather than new. See docs/DECISIONS.md
   D-004.
2. `assert_club_appearances`: every club appears exactly 2(n-1) times per
   season.
3. `assert_source_agreement`: where two sources cover the same match, the
   scorelines match. Disagreements are listed, never averaged. A single revised
   scoreline is a quick approval; many at once means a parser broke.
4. `assert_registry_coverage`: every mart column maps to a `metrics.yml` entry
   and every entry maps to a mart column. Also checked by
   `scripts/check_registry.py`.
5. `assert_tier_honesty`: no metric emits a non-null value before its declared
   `available_from`.

## Tests on every model

- Grain uniqueness and `not_null` on the grain columns, never on the metric.
- Referential integrity to parent grains: every appearance resolves to a person
  and a match, every match to two clubs and a season.
- `accepted_values` on enumerated columns, `accepted_range` where a metric has a
  real bound.
- Do not widen a failing test to make it pass. Do not add a `where` clause or a
  severity override that narrows a test until it is green. Fix the model.

## When to stop

Stop and hand back to Hanna on any of these, per CLAUDE.md:

- A new data source, or a change to a source's terms status or ingest surface.
- A new metric definition, or a change to an existing one.
- Any edit to `pipeline/registry/clubs.yml` or `people.yml`.
- A composite metric with no reviewed notebook under `notebooks/`. Do not invent
  the definition.
