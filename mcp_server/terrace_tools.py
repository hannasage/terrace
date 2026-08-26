"""
Terrace query tools.

Deterministic functions over the published, verified data. These are the coded
tooling the plan calls for: the MCP server in server.py is a thin wrapper that
exposes them to Claude, and these functions carry all the logic so they can be
tested without the MCP transport.

Two honesty rules run through every function, straight from the operating
principles: a metric appears only because it is declared in metrics.yml (the
tools are registry-driven, never hardcoded), and a value outside a metric's range
or a season a club did not play comes back as an explicit gap, never a zero.
Every function names its sources. No model runs here; the tools compute, the
agent narrates.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import yaml

# Data locations. They default to the repo layout, so local Desktop and Code use
# needs no configuration. A remote host that bundles the data elsewhere overrides
# them: TERRACE_DATA_DIR points at the directory holding the published Parquet,
# and TERRACE_METRICS at metrics.yml. This is the only indirection the server
# needs to run off a different filesystem.
REPO = Path(__file__).resolve().parents[1]
PUBLISHED = Path(
    os.environ.get("TERRACE_DATA_DIR", REPO / "pipeline" / "data" / "published")
)
METRICS_YML = Path(
    os.environ.get("TERRACE_METRICS", REPO / "pipeline" / "registry" / "metrics.yml")
)
CLUB_SEASON = PUBLISHED / "club_season.parquet"
CLUB_MATCH = PUBLISHED / "club_match.parquet"
CLUBS = PUBLISHED / "clubs.parquet"

SOURCES = ["engsoccerdata", "football-data"]


def _connect() -> duckdb.DuckDBPyConnection:
    """An in-memory DuckDB connection. The Parquet files are read through
    read_parquet in each query, never opened as a database."""
    return duckdb.connect()


def _load_metrics() -> dict[str, dict]:
    """Active metrics from the registry, keyed by id. Commented entries in the
    YAML are absent by construction, so only live metrics are ever offered."""
    entries = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8")) or []
    return {m["id"]: m for m in entries}


def _season_label(start_year: int) -> str:
    """1992 -> '1992/93'."""
    return f"{start_year}/{str((start_year + 1) % 100).zfill(2)}"


def list_metrics() -> dict:
    """Every metric the tools can return, from metrics.yml.

    Each carries its kind (observed or constructed), so a report can label a
    constructed value as constructed, and the season it becomes available.
    """
    metrics = _load_metrics()
    return {
        "metrics": [
            {
                "id": m["id"],
                "label": m["label"],
                "grain": m["grain"],
                "unit": m["unit"],
                "kind": m["kind"],
                "available_from": m["available_from"],
                "higher_is_better": m.get("higher_is_better"),
                "definition": m.get("definition_url"),
            }
            for m in metrics.values()
        ],
        "sources": SOURCES,
    }


def list_clubs() -> dict:
    """Every canonical club the data holds."""
    con = _connect()
    rows = con.execute(
        "select club_id, club_name, nation from read_parquet(?) order by club_name",
        [CLUBS.as_posix()],
    ).fetchall()
    con.close()
    return {
        "clubs": [
            {"club_id": r[0], "club_name": r[1], "nation": r[2]} for r in rows
        ]
    }


def _resolve_club(con: duckdb.DuckDBPyConnection, club: str) -> tuple[str, str] | None:
    """Resolve a club id or name (case-insensitive) to (id, name), or None."""
    row = con.execute(
        """
        select club_id, club_name from read_parquet(?)
        where club_id = ? or lower(club_name) = lower(?)
        limit 1
        """,
        [CLUBS.as_posix(), club, club],
    ).fetchone()
    return (row[0], row[1]) if row else None


def get_metric(
    club: str,
    metric: str,
    season_from: int | None = None,
    season_to: int | None = None,
) -> dict:
    """A metric's value for one club over a season range.

    Returns one entry per season in range. A season the club did not play in the
    Premier League is returned with value null and a reason, so a gap stays a gap.
    A season before the metric's available_from is likewise a labelled gap.
    """
    metrics = _load_metrics()
    if metric not in metrics:
        return {"error": f"Unknown metric '{metric}'. Call list_metrics for the set."}
    meta = metrics[metric]

    con = _connect()
    resolved = _resolve_club(con, club)
    if resolved is None:
        con.close()
        return {"error": f"Unknown club '{club}'. Call list_clubs for the set."}
    club_id, club_name = resolved

    lo, hi = con.execute(
        "select min(season_start_year), max(season_start_year) from read_parquet(?)",
        [CLUB_SEASON.as_posix()],
    ).fetchone()
    con.close()
    season_from = season_from or lo
    season_to = season_to or hi
    available_from = int(str(meta["available_from"])[:4])

    con = _connect()
    present = dict(
        con.execute(
            f"""
            select season_start_year, {metric}
            from read_parquet(?)
            where club_id = ?
              and season_start_year between ? and ?
            """,
            [CLUB_SEASON.as_posix(), club_id, season_from, season_to],
        ).fetchall()
    )
    con.close()

    series = []
    for year in range(season_from, season_to + 1):
        if year < available_from:
            series.append(
                {
                    "season": _season_label(year),
                    "value": None,
                    "gap": f"before the metric is available ({meta['available_from']})",
                }
            )
        elif year in present:
            series.append({"season": _season_label(year), "value": present[year]})
        else:
            series.append(
                {
                    "season": _season_label(year),
                    "value": None,
                    "gap": "the club did not play in the Premier League this season",
                }
            )

    return {
        "club": club_name,
        "metric": meta["label"],
        "kind": meta["kind"],
        "unit": meta["unit"],
        "definition": meta.get("definition_url"),
        "sources": meta.get("sources", SOURCES),
        "series": series,
    }


def compare(
    clubs: list[str],
    metric: str,
    season_from: int | None = None,
    season_to: int | None = None,
) -> dict:
    """The same metric for two or more clubs over a season range, aligned by
    season so a report can place them side by side. Gaps are preserved per club."""
    if len(clubs) < 2:
        return {"error": "compare needs at least two clubs."}
    results = [get_metric(c, metric, season_from, season_to) for c in clubs]
    errors = [r["error"] for r in results if "error" in r]
    if errors:
        return {"error": "; ".join(errors)}
    return {
        "metric": results[0]["metric"],
        "kind": results[0]["kind"],
        "unit": results[0]["unit"],
        "definition": results[0].get("definition"),
        "sources": results[0]["sources"],
        "clubs": [
            {"club": r["club"], "series": r["series"]} for r in results
        ],
    }


def _match_rows(con: duckdb.DuckDBPyConnection, where: str, args: list) -> list[dict]:
    """Fixtures from one club's perspective, oldest first."""
    rows = con.execute(
        f"""
        select season_start_year, match_date, club_name, opponent_name,
               was_home, goals_for, goals_against, goal_margin, result
        from read_parquet(?)
        where {where}
        order by match_date, match_id
        """,
        [CLUB_MATCH.as_posix(), *args],
    ).fetchall()
    return [
        {
            "season": _season_label(r[0]),
            # Parquet hands the date back as a date or a string depending on the
            # reader, so normalise rather than assuming one of them.
            "date": (
                r[1].isoformat() if hasattr(r[1], "isoformat") else r[1]
            ),
            "club": r[2],
            "opponent": r[3],
            "venue": "home" if r[4] else "away",
            "goals_for": r[5],
            "goals_against": r[6],
            "score": f"{r[5]}-{r[6]}",
            "goal_margin": r[7],
            "result": r[8],
        }
        for r in rows
    ]


def _tally(fixtures: list[dict]) -> dict:
    """Wins, draws, losses and goals from the perspective the fixtures are in."""
    return {
        "played": len(fixtures),
        "won": sum(1 for f in fixtures if f["result"] == "W"),
        "drawn": sum(1 for f in fixtures if f["result"] == "D"),
        "lost": sum(1 for f in fixtures if f["result"] == "L"),
        "goals_for": sum(f["goals_for"] for f in fixtures),
        "goals_against": sum(f["goals_against"] for f in fixtures),
    }


def head_to_head(
    club_a: str,
    club_b: str,
    season_from: int | None = None,
    season_to: int | None = None,
) -> dict:
    """Every league meeting between two clubs, with the record from both sides.

    Premier League fixtures only. A season either club spent outside the division
    has no fixtures, and that absence is reported as a gap rather than as a run of
    goalless draws.
    """
    if club_a.strip().lower() == club_b.strip().lower():
        return {"error": "head_to_head needs two different clubs."}

    con = _connect()
    a = _resolve_club(con, club_a)
    b = _resolve_club(con, club_b)
    if a is None or b is None:
        unknown = club_a if a is None else club_b
        con.close()
        return {"error": f"Unknown club '{unknown}'. Call list_clubs for the set."}
    a_id, a_name = a
    b_id, b_name = b

    lo, hi = con.execute(
        "select min(season_start_year), max(season_start_year) from read_parquet(?)",
        [CLUB_MATCH.as_posix()],
    ).fetchone()
    season_from = season_from or lo
    season_to = season_to or hi

    fixtures = _match_rows(
        con,
        "club_id = ? and opponent_club_id = ? "
        "and season_start_year between ? and ?",
        [a_id, b_id, season_from, season_to],
    )
    con.close()

    # Seasons in range where the two never met. Either one was outside the
    # division or the fixture has not been played yet, and the two are different
    # findings, so the reason says which.
    played_in = {f["season"] for f in fixtures}
    gaps = [
        {
            "season": _season_label(year),
            "gap": (
                "the fixture has not been played yet this season"
                if year == hi
                else "the clubs were not both in the Premier League this season"
            ),
        }
        for year in range(season_from, season_to + 1)
        if _season_label(year) not in played_in
    ]

    tally = _tally(fixtures)
    mirrored = {
        "played": tally["played"],
        "won": tally["lost"],
        "drawn": tally["drawn"],
        "lost": tally["won"],
        "goals_for": tally["goals_against"],
        "goals_against": tally["goals_for"],
    }

    return {
        "clubs": [a_name, b_name],
        "seasons": [_season_label(season_from), _season_label(season_to)],
        "record": {a_name: tally, b_name: mirrored},
        "fixtures": fixtures,
        "gaps": gaps,
        "sources": SOURCES,
        "note": (
            "Premier League meetings only. Cup ties and seasons either club spent "
            "outside the division are not held."
        ),
    }


def club_matches(club: str, season: int) -> dict:
    """Every Premier League fixture a club played in one season, oldest first.

    season is the start year, so 2025 is 2025/26. A club that did not play that
    season comes back with no fixtures and a reason.
    """
    con = _connect()
    resolved = _resolve_club(con, club)
    if resolved is None:
        con.close()
        return {"error": f"Unknown club '{club}'. Call list_clubs for the set."}
    club_id, club_name = resolved

    fixtures = _match_rows(
        con,
        "club_id = ? and season_start_year = ?",
        [club_id, season],
    )
    con.close()

    if not fixtures:
        return {
            "club": club_name,
            "season": _season_label(season),
            "fixtures": [],
            "gap": "the club did not play in the Premier League this season",
            "sources": SOURCES,
        }

    return {
        "club": club_name,
        "season": _season_label(season),
        "record": _tally(fixtures),
        "fixtures": fixtures,
        "sources": SOURCES,
    }
