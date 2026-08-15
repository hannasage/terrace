#!/usr/bin/env python3
"""
Propose canonical club entries from the engsoccerdata snapshot.

Offline tooling to help seed pipeline/registry/clubs.yml, which is hand
maintained and which this script never writes. It reads the latest engsoccerdata
snapshot, lists every distinct club name across the home and visitor columns
with enough context to judge each one, flags names that would collapse to the
same id, and prints a clubs.yml block to paste after review.

Duplicate detection is deterministic. Two names are flagged only when they
normalise to the same id, never by similarity or edit distance, so this stays
inside the no-fuzzy-matching rule in SPEC.md 3 and CLAUDE.md.

Usage:
    uv run python scripts/propose_clubs.py --scope pl     # clubs seen in tier 1 since 1992
    uv run python scripts/propose_clubs.py --scope all    # every club in the file
    uv run python scripts/propose_clubs.py --snapshot <path/to/england.csv[.gz]>

The report goes to stderr, the YAML to stdout, so `> clubs.block.yml` captures
only the block.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = REPO / "pipeline" / "data" / "raw" / "engsoccerdata"

# 1992/93 is Season 1992 in engsoccerdata, the first Premier League season.
PL_FIRST_SEASON = 1992


def latest_snapshot() -> Path:
    """Find the newest dated england snapshot, compressed or not."""
    if not SNAPSHOT_ROOT.exists():
        raise SystemExit(
            f"No snapshot directory at {SNAPSHOT_ROOT}. Run `make ingest` first."
        )
    candidates: list[Path] = []
    for dated in sorted(SNAPSHOT_ROOT.iterdir(), reverse=True):
        for name in ("england.csv.gz", "england.csv"):
            path = dated / name
            if path.exists():
                candidates.append(path)
    if not candidates:
        raise SystemExit(f"No england.csv[.gz] under {SNAPSHOT_ROOT}.")
    return candidates[0]


def slugify(name: str) -> str:
    """Deterministic id from a club name: ascii, lowercase, underscores."""
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
    return slug


def collect(snapshot: Path) -> list[dict]:
    """One row per distinct club name with context."""
    rows = duckdb.sql(
        f"""
        WITH matches AS (
            SELECT * FROM read_csv_auto('{snapshot.as_posix()}')
        ),
        appearances AS (
            SELECT home AS club, Season AS season, tier FROM matches
            UNION ALL
            SELECT visitor AS club, Season AS season, tier FROM matches
        )
        SELECT
            club,
            count(*)                                                   AS matches,
            min(season)                                                AS first_season,
            max(season)                                                AS last_season,
            count(DISTINCT season)                                     AS seasons,
            min(tier)                                                  AS top_tier,
            max(CASE WHEN tier = 1 AND season >= {PL_FIRST_SEASON}
                     THEN 1 ELSE 0 END)                                AS pl_era
        FROM appearances
        GROUP BY club
        ORDER BY club
        """
    ).fetchall()
    columns = [
        "club",
        "matches",
        "first_season",
        "last_season",
        "seasons",
        "top_tier",
        "pl_era",
    ]
    return [dict(zip(columns, row)) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=["all", "pl"],
        default="pl",
        help="pl: clubs seen in tier 1 since 1992. all: every club in the file.",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help="Path to an england.csv or england.csv.gz. Defaults to the latest.",
    )
    args = parser.parse_args()

    snapshot = args.snapshot or latest_snapshot()
    clubs = collect(snapshot)
    selected = [c for c in clubs if args.scope == "all" or c["pl_era"]]

    # Deterministic duplicate flag: names sharing one id.
    by_id: dict[str, list[str]] = {}
    for club in selected:
        by_id.setdefault(slugify(club["club"]), []).append(club["club"])
    collisions = {slug: names for slug, names in by_id.items() if len(names) > 1}

    # Report to stderr.
    print(f"snapshot: {snapshot.relative_to(REPO)}", file=sys.stderr)
    print(f"distinct clubs in file: {len(clubs)}", file=sys.stderr)
    print(f"clubs in scope '{args.scope}': {len(selected)}", file=sys.stderr)
    if collisions:
        print(
            f"\nDUPLICATE IDS ({len(collisions)}), resolve before pasting:",
            file=sys.stderr,
        )
        for slug, names in sorted(collisions.items()):
            print(f"  {slug}: {names}", file=sys.stderr)
    else:
        print("no id collisions in scope.", file=sys.stderr)

    # YAML block to stdout.
    print(f"# clubs.yml, proposal from {snapshot.relative_to(REPO)}")
    print(f"# scope: {args.scope}. Review names and ids before pasting.")
    print(f"# {len(selected)} clubs. Aliases belong in aliases.engsoccerdata.yml.")
    for club in selected:
        note = f"  # {club['matches']} matches, {club['first_season']}-{club['last_season']}, top tier {club['top_tier']}"
        print(f"- id: {slugify(club['club'])}")
        print(f"  name: {club['club']}{note}")


if __name__ == "__main__":
    main()
