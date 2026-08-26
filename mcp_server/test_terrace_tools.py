"""
Tests for the Terrace query tools.

These verify the tool logic against the published Parquet, so the behaviour the
MCP server exposes is checked without the MCP transport. They need the published
artefacts to exist (make build && make publish), which CI does before running.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terrace_tools as tools  # noqa: E402

pytestmark = pytest.mark.skipif(
    not tools.CLUB_SEASON.exists(),
    reason="published artefacts absent; run make build && make publish first",
)


def _value(series: list[dict], season: str):
    return next(s["value"] for s in series if s["season"] == season)


def test_list_metrics_is_registry_driven():
    ids = {m["id"] for m in tools.list_metrics()["metrics"]}
    # the declared metrics are present; a metric that is not in the registry
    # (xG needs an Understat adapter we do not have) is not offered
    assert {"points", "points_per_game", "league_position", "clean_sheets"} <= ids
    assert "expected_goals" not in ids


def test_metric_kind_is_reported():
    metrics = {m["id"]: m for m in tools.list_metrics()["metrics"]}
    assert metrics["points"]["kind"] == "constructed"
    assert metrics["goals_for"]["kind"] == "observed"


def test_known_value_invincibles():
    r = tools.get_metric("Arsenal", "points", 2003, 2003)
    assert _value(r["series"], "2003/04") == 90


def test_champion_is_position_one():
    r = tools.get_metric("Leicester City", "league_position", 2015, 2015)
    assert _value(r["series"], "2015/16") == 1


def test_gap_is_a_gap_not_a_zero():
    # Luton Town played the Premier League only in 2023/24
    r = tools.get_metric("Luton Town", "points", 2021, 2024)
    played = _value(r["series"], "2023/24")
    absent = next(s for s in r["series"] if s["season"] == "2021/22")
    assert played == 26
    assert absent["value"] is None
    assert "gap" in absent


def test_club_name_is_case_insensitive():
    r = tools.get_metric("arsenal", "points", 2003, 2003)
    assert "error" not in r


def test_unknown_metric_and_club_error_clearly():
    assert "error" in tools.get_metric("Arsenal", "expected_goals", 2020, 2020)
    assert "error" in tools.get_metric("Nowhere United", "points", 2020, 2020)


def test_compare_aligns_by_season():
    c = tools.compare(["Arsenal", "Tottenham Hotspur"], "points", 2015, 2016)
    assert len(c["clubs"]) == 2
    assert {club["club"] for club in c["clubs"]} == {"Arsenal", "Tottenham Hotspur"}


def test_compare_needs_two_clubs():
    assert "error" in tools.compare(["Arsenal"], "points")
