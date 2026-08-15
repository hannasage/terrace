"""
engsoccerdata adapter.

Fetches the England results CSV and writes it to a dated, immutable snapshot,
but only when the source has changed since the last one. engsoccerdata is a
single monolithic file with no way to ask for just the new rows, so "only fetch
updates" is achieved two ways: a conditional request that returns 304 and no
body when nothing changed, and a content hash that guards against storing an
identical file even if the server answers 200. Historic seasons never move, so
most refreshes cost one small 304 and write nothing.

The fetch is deliberately dumb: it captures bytes and records a position. Parsing
and club-name resolution happen later in dbt, per SPEC.md 4.5 and DECISIONS
D-009. The snapshot is stored gzip compressed, which DuckDB reads directly, to
keep the data lane small.

Source register entry: docs/DATA-SOURCES.md, engsoccerdata.
"""

from __future__ import annotations

import gzip
import hashlib
import urllib.error
import urllib.request
from pathlib import Path

SOURCE_ID = "engsoccerdata"

# Raw CSV on the jalapic/engsoccerdata default branch. The host is on the ingest
# allowlist in .claude/hooks/guardrails.py. Verified 2026-08-15: the file lives
# on master, is roughly 15 MB, and raw.githubusercontent.com serves a content
# ETag and honours If-None-Match with a 304.
URL = (
    "https://raw.githubusercontent.com/jalapic/engsoccerdata/master/"
    "data-raw/england.csv"
)

FILENAME = "england.csv.gz"
TIMEOUT_SECONDS = 60


def _conditional_get(url: str, etag: str | None) -> tuple[bytes | None, str | None]:
    """Fetch url, sending the stored ETag. Returns (body, etag).

    body is None when the server answers 304 Not Modified, meaning the source is
    unchanged and nothing was downloaded. Any status other than 200 or 304 fails
    loud.
    """
    headers = {"User-Agent": "terrace-ingest"}
    if etag:
        headers["If-None-Match"] = etag
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"{SOURCE_ID}: expected HTTP 200 from {url}, got {response.status}"
                )
            return response.read(), response.headers.get("ETag")
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return None, etag
        raise


def fetch(run_date: str, raw_root: Path, state: dict) -> tuple[bool, dict]:
    """Capture a snapshot if the source changed. Returns (changed, new_state).

    When unchanged, returns (False, state) and writes nothing. When changed,
    writes a gzip snapshot under pipeline/data/raw/<source>/<run_date>/ and
    returns the new state to record. A snapshot is never overwritten: if one
    already exists for this run date, the existing capture stands.
    """
    body, etag = _conditional_get(URL, state.get("etag"))
    if body is None:
        return False, state

    digest = hashlib.sha256(body).hexdigest()
    if digest == state.get("content_sha256"):
        # The server answered 200 but the content matches the last snapshot.
        return False, state

    dest_dir = raw_root / SOURCE_ID / run_date
    dest = dest_dir / FILENAME
    if dest.exists():
        return False, state

    dest_dir.mkdir(parents=True, exist_ok=True)
    # mtime 0 keeps the gzip header stable, so identical input gives identical
    # bytes and the store carries no wall-clock noise.
    dest.write_bytes(gzip.compress(body, compresslevel=9, mtime=0))

    new_state = {
        "source": SOURCE_ID,
        "url": URL,
        "last_changed_run_date": run_date,
        "snapshot": f"{SOURCE_ID}/{run_date}/{FILENAME}",
        "content_sha256": digest,
        "etag": etag,
        "uncompressed_bytes": len(body),
    }
    return True, new_state
