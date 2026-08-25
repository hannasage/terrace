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


def write_parquet(rows: list[dict], name: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / name
    con = duckdb.connect()
    # Build the table via parameterised inserts to avoid a pandas dependency.
    con.execute("CREATE TABLE t (club_id VARCHAR, club_name VARCHAR, nation VARCHAR)")
    con.executemany(
        "INSERT INTO t VALUES (?, ?, ?)",
        [(r["club_id"], r["club_name"], r["nation"]) for r in rows],
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
    dest = write_parquet(clubs, "clubs.parquet")
    print(f"Wrote {len(clubs)} clubs to {dest.relative_to(REPO)}.")


if __name__ == "__main__":
    main()
