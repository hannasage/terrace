---
name: add-transformer
description: Use when adding a new metric to Terrace, whether observed or constructed. Covers the full sequence from reading the notebook definition through registry entry, dbt model, tests, documentation and review. Trigger on requests like "add a metric", "implement the composite from the notebook", "expose X in the comparison builder", or "add a new transformer".
---

# Adding a metric

Every number the application can plot is a metric. Adding one is the same
sequence every time. The interface picks it up automatically, so there is never
a matching change under `web/`.

If there is a matching change under `web/`, something is wrong. Stop and say so.

## 0. Establish the definition

A metric enters the pipeline with a definition that already exists. Two cases:

**Observed.** A value that appears in a source, possibly renamed or rescaled.
The definition is the source field and its units.

**Constructed.** Anything derived, including a simple ratio. The definition
comes from a reviewed notebook under `notebooks/`, which supplies the formula,
the constants, the normalisation, and reference values to test against.

If a constructed metric has no notebook, stop. Do not invent the definition.
Say what is missing and hand it back.

## 1. Registry entry

Draft the entry in `pipeline/registry/metrics.yml`:

```yaml
- id: <snake_case_id>
  label: <human label, sentence case>
  grain: <club_season | person_season | match | appearance>
  unit: <count | per_90 | per_match | ratio | rating | currency>
  kind: <observed | constructed>
  available_from: "<YYYY-YY>"
  sources: [<source ids from docs/DATA-SOURCES.md>]
  definition_url: docs/metrics/<id>.md
  higher_is_better: <true | false | null>
  precision: <integer>
```

Rules that get this wrong most often:

- `kind` is `constructed` for anything derived, including goals per 90. If the
  number does not appear in a source exactly as published, it is constructed.
- `available_from` is the earliest season where **every** input exists, not the
  earliest season where the output happens to compute. A ratio needing xG
  starts at 2014-15 regardless of what the denominator supports.
- `higher_is_better` is `null` for genuinely neutral metrics such as average
  age. Do not force a direction.

A new entry is a proposal until Hanna approves it. Draft it, then stop for
approval before step 2 if the metric is constructed. Observed metrics may
proceed.

## 2. Definition document

Write `docs/metrics/<id>.md` containing:

- One-sentence plain definition
- The formula, with every constant printed
- Which inputs come from which source
- Why `available_from` is what it is
- For constructed metrics: the normative choices made and who made them
- Known limitations, and the seasons where the metric is thin or unstable
- For composites: a link to the notebook and its review

This file is linked from the interface wherever the metric appears. Write it for
someone who will read it after being surprised by a chart.

## 3. dbt model

Add or extend the mart model at the declared grain.

- Compute from `core`, never from `staging` or raw
- Emit `NULL` before `available_from`, by construction rather than by filter
- Keep signs. A negative goal difference stays negative
- No `COALESCE` that turns a missing input into a present output

## 4. Tests

Add to the model's schema file:

- `not_null` on the grain columns, never on the metric itself
- `accepted_range` where the metric has a real bound
- A tier-honesty assertion: the metric is null for every season before
  `available_from`

For constructed metrics, add a singular test comparing the model output to the
notebook's reference values for a named set of entities and seasons, to a stated
tolerance. This is the test that catches a transcription error in a constant,
and it is the reason the notebook must publish reference values.

## 5. Verify

```
make build      # dbt build including all tests
make check      # quality gates, lint, typecheck
make publish    # regenerate Parquet artefacts
make dev        # confirm the metric appears in the comparison builder
```

The metric should now be selectable, correctly labelled, correctly bounded by
season, and marked constructed if it is. You changed nothing under `web/` to
achieve that.

## 6. Review

Run the `data-quality-reviewer` subagent over the change before proposing it as
complete. Address blocking findings. Report should-fix findings you chose not to
address, with the reason.

## 7. Record

Add a `docs/DECISIONS.md` entry only if the metric involved a normative choice
worth preserving, such as a weighting or a chosen normalisation. Routine
observed metrics do not need one.

## Common failures

- Implementing a composite slightly differently from the notebook because the
  notebook version looked inefficient. The definition is the contract.
- Setting `available_from` from the output rather than the scarcest input.
- Marking a per-90 rate as observed.
- Adding a metric picker option under `web/` because the registry-driven path
  seemed slower to get working.
- Widening a failing test instead of fixing the model.
