"""
football-data.co.uk adapter.

Fetches the Premier League results CSV for each season and writes gzip snapshots,
but only for seasons that have changed since the last run. This is where the
per-source reference point in D-010 earns its keep: football-data is partitioned
by season, so the state carries one ETag per season. A completed season's file
never changes again, so it answers 304 forever after its first capture; only the
current season is re-fetched in earnest. That is genuine incrementality, not a
whole-file re-download.

The bare domain is used deliberately: it matches the host on the ingest allowlist
in .claude/hooks/guardrails.py exactly, and it serves the same files as the www
host with conditional-request support.

The fetch is dumb: it captures bytes per season and records a position. Parsing,
club-name resolution and cross-source agreement happen later in dbt, per D-009.

Source register entry: docs/DATA-SOURCES.md, football-data.co.uk. Role: primary
results and match statistics from 1993/94.
"""

from __future__ import annotations

import gzip
import hashlib
import time
import urllib.error
import urllib.request
from pathlib import Path

SOURCE_ID = "football-data"

# Premier League division file (E0) per season. Host is on the ingest allowlist.
# Verified 2026-08-16: serves a content ETag and answers If-None-Match with 304.
URL_TEMPLATE = "https://football-data.co.uk/mmz4281/{code}/E0.csv"

# The Premier League's first season under football-data coverage.
FIRST_SEASON_START = 1993
TIMEOUT_SECONDS = 60

# This adapter makes one request per season, so a full run is dozens of requests
# to one host. Fetch politely, per docs/DATA-SOURCES.md: a short gap between
# requests, and a bounded retry on a transient connection reset so an unattended
# scheduled run does not fail on a blip. The delay does not affect output, so it
# does not touch determinism; the same seasons produce the same snapshots.
REQUEST_GAP_SECONDS = 0.3
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2.0


def _season_codes(run_date: str) -> list[str]:
    """Season codes from 1993/94 up to the season current on run_date.

    A code is the two-digit start year and two-digit end year, so 1993/94 is
    9394 and 2000/01 is 0001. The season rolls over in the summer, so a run in
    July or later belongs to the season starting that calendar year. The run
    date is supplied from outside, so this reads no clock.
    """
    year = int(run_date[:4])
    month = int(run_date[5:7])
    latest_start = year if month >= 7 else year - 1
    codes = []
    for start in range(FIRST_SEASON_START, latest_start + 1):
        codes.append(f"{start % 100:02d}{(start + 1) % 100:02d}")
    return codes


# Distinct outcomes for a season fetch, kept separate from the (body, etag)
# success tuple so there is no chance of a sentinel string being unpacked as a
# body. NOT_MODIFIED means a 304, MISSING means a 404.
NOT_MODIFIED = "not_modified"
MISSING = "missing"


def _fetch_season(code: str, etag: str | None):
    """Return (body, etag) on 200, NOT_MODIFIED on 304, or MISSING on 404.

    Any other status fails loud.
    """
    headers = {"User-Agent": "terrace-ingest"}
    if etag:
        headers["If-None-Match"] = etag
    url = URL_TEMPLATE.format(code=code)
    request = urllib.request.Request(url, headers=headers)

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"{SOURCE_ID}: expected HTTP 200 for season {code}, got "
                        f"{response.status}"
                    )
                return response.read(), response.headers.get("ETag")
        except urllib.error.HTTPError as exc:
            # A status answer is not transient. Do not retry it.
            if exc.code == 304:
                return NOT_MODIFIED
            if exc.code == 404:
                return MISSING
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
            # A dropped or reset connection is transient. Back off and retry.
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise RuntimeError(
        f"{SOURCE_ID}: season {code} failed after {MAX_ATTEMPTS} attempts "
        f"({last_error})."
    )


def fetch(run_date: str, raw_root: Path, state: dict) -> tuple[bool, dict]:
    """Capture any season that changed. Returns (changed, new_state).

    Each changed season is written to
    pipeline/data/raw/football-data/<run_date>/E0_<code>.csv.gz. A 404 on the
    newest season is allowed, since a season that has not started yet has no
    file; a 404 on any earlier season fails the run, because a completed season
    must exist.
    """
    codes = _season_codes(run_date)
    if not codes:
        return False, state
    newest = codes[-1]

    prior_seasons: dict = dict(state.get("seasons", {}))
    seasons = dict(prior_seasons)
    changed = False

    for index, code in enumerate(codes):
        if index:
            time.sleep(REQUEST_GAP_SECONDS)
        prior = prior_seasons.get(code, {})
        result = _fetch_season(code, prior.get("etag"))

        if result == NOT_MODIFIED:
            continue
        if result == MISSING:
            if code == newest:
                continue
            raise RuntimeError(
                f"{SOURCE_ID}: season {code} returned 404 but should exist."
            )

        body, etag = result
        digest = hashlib.sha256(body).hexdigest()
        if digest == prior.get("content_sha256"):
            continue

        dest_dir = raw_root / SOURCE_ID / run_date
        dest = dest_dir / f"E0_{code}.csv.gz"
        if dest.exists():
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(gzip.compress(body, compresslevel=9, mtime=0))

        seasons[code] = {
            "etag": etag,
            "content_sha256": digest,
            "snapshot": f"{SOURCE_ID}/{run_date}/E0_{code}.csv.gz",
        }
        changed = True

    if not changed:
        return False, state

    new_state = {
        "source": SOURCE_ID,
        "last_changed_run_date": run_date,
        "url_template": URL_TEMPLATE,
        "seasons": seasons,
    }
    return True, new_state
