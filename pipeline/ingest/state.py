"""
Per-source ingest state.

Each source keeps a small JSON file at pipeline/data/state/<source>.json that
records what was last captured: the validator the source hands back (an ETag),
a content hash, and where the snapshot landed. This is the reference point a
refresh compares against, so a source is only re-fetched or re-stored when it
has actually moved since the last snapshot.

The state file is operational metadata, a pointer to the current position, not a
snapshot. Snapshots are immutable and dated; this file is overwritten each time
the source changes, and left untouched when it does not. It is committed so the
next run, on a fresh checkout, starts from the last known position rather than
from nothing.
"""

from __future__ import annotations

import json
from pathlib import Path


def state_path(source: str, raw_root: Path) -> Path:
    """pipeline/data/state/<source>.json, given raw_root of pipeline/data/raw."""
    return raw_root.parent / "state" / f"{source}.json"


def load_state(source: str, raw_root: Path) -> dict:
    """Return the recorded state for a source, or an empty dict if none yet."""
    path = state_path(source, raw_root)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_state(source: str, raw_root: Path, state: dict) -> None:
    """Write the source state, sorted and stable so diffs stay small."""
    path = state_path(source, raw_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
