#!/usr/bin/env python3
"""
Publish verified Parquet artefacts for the local tool layer.

Reads the marts from the dbt-built DuckDB database and writes one Parquet file
per published table into pipeline/data/published/. The local MCP server reads
these files, and the scheduled data-refresh regenerates and commits them, so the
tools always serve the latest verified data without rebuilding.

    python scripts/publish.py            # write the artefacts
    python scripts/publish.py --check    # verify the committed artefacts are current

--check re-derives each table from the current build and compares it to the
committed Parquet by content, not bytes, so Parquet metadata differences never
cause a false failure. Any real drift exits non-zero, which catches a mart change
that was not re-published.

Determinism: reads the built database, writes Parquet, no network and no clock.
There is no export route or endpoint here, only static local files (D-013).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "pipeline" / "dbt" / "terrace.duckdb"
OUT_DIR = REPO / "pipeline" / "data" / "published"

# Each published file and the query that produces it, ordered deterministically.
# club_season carries the club name alongside the id so a report is readable
# without a second lookup; clubs is the dimension on its own.
ARTEFACTS = {
    "club_season.parquet": """
        select
            m.season_start_year,
            m.club_id,
            c.club_name,
            m.matches_played,
            m.wins,
            m.draws,
            m.losses,
            m.goals_for,
            m.goals_against,
            m.goal_difference,
            m.points,
            m.points_per_game,
            m.win_rate,
            m.goals_for_per_game,
            m.goals_against_per_game,
            m.goal_difference_per_game,
            m.points_share,
            m.league_position,
            m.is_champion,
            m.relegated,
            m.points_change_vs_prev,
            m.goal_difference_change_vs_prev,
            m.clean_sheets,
            m.biggest_win_margin,
            m.longest_win_streak
        from mart__club_season m
        join stg_registry__clubs c using (club_id)
        order by m.season_start_year, m.club_id
    """,
    # One row per club per match, both perspectives of every fixture. This is
    # what makes a head-to-head answerable: the club-season grain cannot say who
    # beat whom, only how a season ended. Both club names travel with the row so
    # a report reads without a second lookup, same as club_season.
    "club_match.parquet": """
        select
            m.season_start_year,
            m.match_id,
            m.match_date,
            m.club_id,
            c.club_name,
            m.opponent_club_id,
            o.club_name as opponent_name,
            m.was_home,
            m.goals_for,
            m.goals_against,
            m.goal_margin,
            m.result,
            m.clean_sheet,
            m.match_number
        from mart__club_match m
        join stg_registry__clubs c on c.club_id = m.club_id
        join stg_registry__clubs o on o.club_id = m.opponent_club_id
        order by m.season_start_year, m.match_date, m.match_id, m.club_id
    """,
    "clubs.parquet": """
        select club_id, club_name, nation
        from stg_registry__clubs
        order by club_id
    """,
}


def connect() -> duckdb.DuckDBPyConnection:
    if not DB.exists():
        raise SystemExit(
            f"No built database at {DB.relative_to(REPO)}. Run `make build` first."
        )
    return duckdb.connect(str(DB), read_only=True)


def write() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = connect()
    for name, query in ARTEFACTS.items():
        dest = OUT_DIR / name
        con.execute(
            f"copy ({query}) to '{dest.as_posix()}' (format parquet)"
        )
        rows = con.execute(f"select count(*) from ({query})").fetchone()[0]
        print(f"Wrote {rows} rows to {dest.relative_to(REPO)}.")
    con.close()


def check() -> None:
    con = connect()
    drift = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, query in ARTEFACTS.items():
            committed = OUT_DIR / name
            if not committed.exists():
                drift.append(f"{name}: missing from pipeline/data/published/")
                continue
            fresh = Path(tmp) / name
            con.execute(f"copy ({query}) to '{fresh.as_posix()}' (format parquet)")
            # Compare by content, both directions, so order and metadata do not matter.
            diff = con.execute(
                f"""
                select count(*) from (
                    (select * from read_parquet('{fresh.as_posix()}')
                     except select * from read_parquet('{committed.as_posix()}'))
                    union all
                    (select * from read_parquet('{committed.as_posix()}')
                     except select * from read_parquet('{fresh.as_posix()}'))
                )
                """
            ).fetchone()[0]
            if diff:
                drift.append(f"{name}: {diff} row(s) differ from a fresh build")
    con.close()

    if drift:
        print("Published artefacts are stale:", file=sys.stderr)
        for item in drift:
            print(f"  {item}", file=sys.stderr)
        print(
            "\nRun `make publish` and commit the updated Parquet.", file=sys.stderr
        )
        sys.exit(1)
    print("Published artefacts are current.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the committed artefacts match a fresh build, without writing.",
    )
    args = parser.parse_args()
    check() if args.check else write()
    sys.exit(0)


if __name__ == "__main__":
    main()
