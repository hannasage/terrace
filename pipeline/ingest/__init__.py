"""
Deterministic source ingest for Terrace.

One module per source under this package, each exposing a SOURCE_ID and a
fetch(run_date, raw_root) that writes a dated, immutable snapshot beneath
pipeline/data/raw/<source>/<run_date>/. An adapter never overwrites an existing
snapshot and never mutates in place, so a snapshot is a permanent record of what
a source held on a given day.

The run date is passed in, never read from the clock, so nothing here depends on
wall-clock time. The network fetch lives here in the source layer, never in the
dbt transformation path.

ADAPTERS maps a source id to its fetch function. REGISTERED_SOURCES is every
source recorded in docs/DATA-SOURCES.md, used to tell an unknown source, which
fails the run, from a registered source with no adapter yet, which is reported
and skipped so the data-refresh workflow runs green before every adapter exists.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from . import engsoccerdata

RAW_ROOT = Path(__file__).resolve().parents[2] / "pipeline" / "data" / "raw"

# Sources recorded in docs/DATA-SOURCES.md.
REGISTERED_SOURCES = {
    "engsoccerdata",
    "football-data",
    "understat",
    "fpl",
    "clubelo",
}

# source id -> fetch function. Grows one entry per implemented adapter.
ADAPTERS: dict[str, Callable[[str, Path], bool]] = {
    engsoccerdata.SOURCE_ID: engsoccerdata.fetch,
}

_RUN_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def resolve_sources(requested: str) -> list[str]:
    """Turn a --sources value into a sorted list of known source ids.

    'all' expands to every registered source. Any id that is neither registered
    nor known fails closed, naming the offending value.
    """
    if requested.strip() == "all":
        return sorted(REGISTERED_SOURCES)
    ids = [part.strip() for part in requested.split(",") if part.strip()]
    unknown = [i for i in ids if i not in REGISTERED_SOURCES]
    if unknown:
        raise SystemExit(
            f"Unknown source id(s): {', '.join(unknown)}. Add an entry to "
            "docs/DATA-SOURCES.md and register an adapter, or fix the spelling. "
            "Failing closed."
        )
    return ids


def run(requested: str, run_date: str | None) -> int:
    """Run the requested adapters. Returns the count that wrote a new snapshot."""
    sources = resolve_sources(requested)
    runnable = [s for s in sources if s in ADAPTERS]

    if runnable and not (run_date and _RUN_DATE_RE.match(run_date)):
        raise SystemExit(
            "A run date is required to write a snapshot. Pass --run-date "
            "YYYY-MM-DD, or set TERRACE_RUN_DATE. The pipeline never reads the "
            "clock, so the date is supplied from outside."
        )

    wrote = 0
    for source in sources:
        adapter = ADAPTERS.get(source)
        if adapter is None:
            print(f"[{source}] no adapter implemented yet, skipping.")
            continue
        if adapter(run_date, RAW_ROOT):
            print(f"[{source}] wrote a new snapshot for {run_date}.")
            wrote += 1
        else:
            print(f"[{source}] snapshot for {run_date} already present, skipping.")
    return wrote
