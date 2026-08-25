#!/usr/bin/env python3
"""
Materialise the hand-maintained registry YAML into Parquet for dbt to read.

dbt runs on DuckDB, which reads Parquet but not YAML. The registry
(clubs.<nation>.yml, and later aliases.<source>.yml) stays the single source of
truth, hand-maintained by Hanna; this step converts it into a build artifact the
staging models can join against. The Parquet lives under pipeline/data/registry/
and is gitignored, so it is never committed and never a second source of truth.

Run before every dbt build. The Makefile build target and the CI pipeline job
both call it.

Deterministic: reads committed YAML, writes Parquet, no network and no clock.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import yaml

REPO = Path(__file__).resolve().parents[1]
REGISTRY = REPO / "pipeline" / "registry"
OUT_DIR = REPO / "pipeline" / "data" / "registry"


def load_clubs() -> list[dict]:
    """Every clubs.<nation>.yml, flattened, with the nation recorded."""
    rows: list[dict] = []
    for path in sorted(REGISTRY.glob("clubs.*.yml")):
        nation = path.stem.split(".", 1)[1]  # clubs.eng -> eng
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for entry in entries:
            rows.append(
                {
                    "club_id": entry["id"],
                    "club_name": entry["name"],
                    "nation": nation,
                }
            )
    return rows


def load_aliases() -> list[dict]:
    """Every aliases.<source>.yml, flattened, with the source recorded.

    Each entry maps a source club name to a canonical club id. The source id is
    taken from the filename: aliases.football-data.yml -> football-data.
    """
    rows: list[dict] = []
    for path in sorted(REGISTRY.glob("aliases.*.yml")):
        source = path.stem.split(".", 1)[1]  # aliases.football-data -> football-data
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for entry in entries:
            rows.append(
                {
                    "source": source,
                    "source_name": entry["source_name"],
                    "club_id": entry["club_id"],
                }
            )
    return rows


def write_parquet(rows: list[dict], columns: list[str], name: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / name
    con = duckdb.connect()
    # Build the table via parameterised inserts to avoid a pandas dependency.
    col_defs = ", ".join(f"{c} VARCHAR" for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    con.execute(f"CREATE TABLE t ({col_defs})")
    con.executemany(
        f"INSERT INTO t VALUES ({placeholders})",
        [tuple(r[c] for c in columns) for r in rows],
    )
    con.execute(f"COPY t TO '{dest.as_posix()}' (FORMAT PARQUET)")
    con.close()
    return dest


def main() -> None:
    clubs = load_clubs()
    if not clubs:
        raise SystemExit(
            "No clubs found under pipeline/registry/clubs.*.yml. Seed the "
            "registry before building."
        )
    dest = write_parquet(clubs, ["club_id", "club_name", "nation"], "clubs.parquet")
    print(f"Wrote {len(clubs)} clubs to {dest.relative_to(REPO)}.")

    # Aliases may not exist yet for every source; an empty table is fine, the
    # transform just resolves nothing through it.
    aliases = load_aliases()
    dest = write_parquet(
        aliases, ["source", "source_name", "club_id"], "aliases.parquet"
    )
    print(f"Wrote {len(aliases)} aliases to {dest.relative_to(REPO)}.")


if __name__ == "__main__":
    main()
