# DECISIONS.md

Newest first. Each entry is self-contained. Decisions are superseded by new
entries, never edited away.

Format: ID, date, decision, evidence, what it rules out.

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
