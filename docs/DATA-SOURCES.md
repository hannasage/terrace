# DATA-SOURCES.md

Every source the pipeline touches. A source with no entry here is not permitted
in `pipeline/ingest/`, and the build fails if one appears.

Status values:

- **cleared**: published terms permit this use, or written permission held
- **tolerated**: no permission granted and none refused, use is consistent with
  common practice and with a personal non-commercial posture
- **excluded**: terms prohibit this use, do not touch

Last verified: 13 Aug 2026.

---

## engsoccerdata

- **Role:** historical spine. Sole source for 1992/93. Cross-check for results
  1993/94 onward.
- **Access:** raw CSV at `data-raw/england.csv` in the GitHub repository,
  packaged `.rda` in `data/`.
- **Schema:** results only. Date, Season, home, visitor, FT, hgoal, vgoal,
  division, tier, totgoal, goaldif, result. No match statistics, no players.
- **Coverage verified 2026-08-13:** English tier 1 from 1888 to season 2024
  (2024/25, last match 25 May 2025).
- **Known defects:**
  - 2025/26 absent entirely.
  - **2022/23 missing across all four tiers.** Zero rows. Confirmed in both the
    raw CSV and the packaged binary. Season sequence runs 2021, 2023, 2024.
  - 2019/20 tier 3 and tier 4 are short (400 and 440 matches) because those
    seasons were curtailed. This is correct, not a defect. Do not "fix" it.
- **Cadence:** sporadic, single maintainer. Last push 8 Feb 2026, updating other
  countries mid-season.
- **Licence:** GPL (>= 2) on the R package. Interaction with the bundled data is
  unresolved. Open question in `SPEC.md` section 8.
- **Attribution:** cite James P. Curley, engsoccerdata.
- **Status:** cleared for the code licence, unresolved for the data.

## football-data.co.uk

- **Role:** primary source for results and match statistics.
- **Access:** season CSV files per division, `E0` for the Premier League.
- **Coverage:** 1993/94 onward. Field availability by era:
  - 1993/94 to 1994/95: final scores only
  - 1995/96 to 1999/00: adds half-time scores
  - 2000/01 onward: adds referee, shots, shots on target, fouls, corners, cards
- **Cadence:** at least twice weekly during the season.
- **Terms:** free to download for personal and research use. No published grant
  permitting republication on a third-party site was found; the site carries a
  bare all-rights-reserved notice. Not read directly from their terms page yet.
- **Note:** the site is funded by bookmaker affiliate advertising. Attribution
  by name is required. Whether to link is a deliberate choice, not a default.
- **Status:** tolerated. Personal non-commercial use sits inside what the site
  offers. Permission email drafted but not sent.

## Understat

- **Role:** team and player expected goals, shot level.
- **Access:** JSON embedded in page script tags. Live and current, serving
  2025/26 as of 13 Aug 2026, seasons selectable back to 2014/15.
- **Fields:** xG, npxG, xGA, npxGA, npxGD, PPDA, OPPDA, deep completions, xPTS
  at team level; xG, xA, npxG, xGChain, xGBuildup at player level.
- **Coverage:** 2014/15 onward. Holds 2022/23 correctly, which engsoccerdata
  does not.
- **Terms:** no published terms found in either direction.
- **Rate limiting:** none observed. Fetch politely regardless: sequential, with
  a delay, cached locally, and never re-fetched for a completed season.
- **Status:** tolerated. Permission email drafted but not sent.

## Fantasy Premier League API

- **Role:** player level per gameweek.
- **Access:** unauthenticated JSON. `bootstrap-static` returns all players,
  clubs and gameweeks in one request. Per-player detail and fixtures on
  separate paths. Blocked by CORS for browser calls, so server side only, which
  suits the batch ingest anyway.
- **Coverage:** current season live. Historical seasons from 2016/17 via
  community archives, refreshed a few times per season rather than weekly.
- **Notable fields:** expected goals, expected assists, expected goal
  involvements and expected goals conceded from 2022/23. Defensive contribution
  and clearances-blocks-interceptions from 2025/26.
- **Terms:** governed by Premier League terms of use, which prohibit commercial
  use and the creation of a database from material obtained from the site.
- **Posture required:** free, non-commercial, no export, no redistribution,
  visible non-affiliation notice, working takedown contact.
- **Status:** tolerated, conditional on the posture above holding.

## ClubElo

- **Role:** continuous club strength series.
- **Access:** CSV API. Per-club history and per-date league snapshots.
- **Coverage:** deep, decades before the Premier League era.
- **Terms:** published as a public API for this purpose.
- **Status:** cleared.

---

## Excluded

### FBref and Stathead

**Do not use, for any purpose, including historical backfill.**

Two independent reasons:

1. Sports Reference's data use page states that sites and tools should not be
   built on data scraped from their sites without permission. That is this
   project.
2. On 20 January 2026 Sports Reference removed all advanced soccer data from
   FBref and Stathead after their provider terminated the feed and required
   deletion. The advanced statistics no longer update, so the source is stale as
   well as prohibited.

Rate limits, for completeness: ten requests per minute for FBref and Stathead.
Irrelevant, since we do not fetch from them at all.

### Premier League official site scraping

Prohibited by the same terms that cover the fantasy API, with none of the
tolerated-practice cover. The fantasy endpoints are the permitted-in-practice
path to the same underlying facts.

---

## Adding a source

1. Open a decision entry in `docs/DECISIONS.md` proposing it.
2. Record role, access method, coverage, cadence, terms, and status here.
3. Hanna approves.
4. Only then write the ingest module.

Claude Code may draft steps 1 and 2 and must stop before step 4.
