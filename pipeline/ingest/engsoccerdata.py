"""
engsoccerdata adapter.

Downloads the England results CSV and writes it to a dated, immutable snapshot.
This is a fetch and a byte-for-byte capture, nothing more. Parsing, type
coercion and club-name resolution happen later in the dbt staging and core
layers, which is where an unrecognised name fails the build per SPEC.md 4.5.
Keeping the fetch dumb is what lets it stay deterministic: the same URL on the
same day produces the same snapshot, and a snapshot once written is never
touched again.

Source register entry: docs/DATA-SOURCES.md, engsoccerdata. Role: historical
spine, sole source for 1992/93, cross-check thereafter.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

SOURCE_ID = "engsoccerdata"

# Raw CSV on the jalapic/engsoccerdata default branch. The host is on the
# ingest allowlist in .claude/hooks/guardrails.py. Verified 2026-08-15: the
# file lives on master, not main, and is roughly 15 MB.
URL = (
    "https://raw.githubusercontent.com/jalapic/engsoccerdata/master/"
    "data-raw/england.csv"
)

FILENAME = "england.csv"
TIMEOUT_SECONDS = 60


def _download(url: str) -> bytes:
    """Fetch the URL, failing loud on any non-200 response."""
    request = urllib.request.Request(url, headers={"User-Agent": "terrace-ingest"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(
                f"{SOURCE_ID}: expected HTTP 200 from {url}, got {response.status}"
            )
        return response.read()


def fetch(run_date: str, raw_root: Path) -> bool:
    """Write a dated snapshot. Returns True if a new snapshot was written.

    A snapshot is immutable. If one already exists for this run date, the
    adapter does nothing and returns False, so re-running a refresh on the same
    day never rewrites history.
    """
    dest_dir = raw_root / SOURCE_ID / run_date
    dest = dest_dir / FILENAME
    if dest.exists():
        return False

    payload = _download(URL)
    if not payload:
        raise RuntimeError(f"{SOURCE_ID}: downloaded an empty file from {URL}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    return True
