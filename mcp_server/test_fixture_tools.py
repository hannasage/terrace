"""
Tests for the fixture level tools.

These are the tools that make a head-to-head answerable. The club-season marts
hold how a season ended, not who won a given match, so before these existed the
honest answer to "Villa against Arsenal" was a refusal.

Facts here are checked against the published data, and the known ones against
the historical record.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terrace_tools as tools  # noqa: E402

pytestmark = pytest.mark.skipif(
    not tools.CLUB_MATCH.exists(),
    reason="published artefacts absent; run make build && make publish first",
)


def test_head_to_head_records_mirror_each_other():
    r = tools.head_to_head("Aston Villa", "Arsenal")
    villa = r["record"]["Aston Villa"]
    arsenal = r["record"]["Arsenal"]
    assert villa["won"] == arsenal["lost"]
    assert villa["lost"] == arsenal["won"]
    assert villa["drawn"] == arsenal["drawn"]
    assert villa["goals_for"] == arsenal["goals_against"]
    assert villa["played"] == arsenal["played"] == len(r["fixtures"])


def test_head_to_head_tally_agrees_with_the_fixtures():
    r = tools.head_to_head("Arsenal", "Manchester United")
    villa = r["record"]["Arsenal"]
    assert villa["won"] == sum(1 for f in r["fixtures"] if f["result"] == "W")
    assert villa["played"] == villa["won"] + villa["drawn"] + villa["lost"]


def test_fixtures_are_ordered_and_dated_sanely():
    """The dates have to be real. football-data writes some with a two-digit
    year, and reading those with a four-digit format dated 8524 matches to the
    first century, which passed a not-null check unnoticed."""
    r = tools.head_to_head("Aston Villa", "Arsenal")
    dates = [f["date"] for f in r["fixtures"]]
    assert all(d is not None for d in dates)
    assert dates == sorted(dates), "fixtures should run oldest first"
    assert dates[0] >= "1992-08-01", dates[0]
    assert all(d <= "2027-12-31" for d in dates)


def test_a_season_out_of_the_division_is_a_gap():
    # Villa spent 2016/17 to 2018/19 outside the Premier League, so there is no
    # meeting to report. That is a gap, not a run of goalless draws.
    r = tools.head_to_head("Aston Villa", "Arsenal")
    gaps = {g["season"]: g["gap"] for g in r["gaps"]}
    assert "2016/17" in gaps
    assert "not both in the Premier League" in gaps["2016/17"]
    assert not any(f["season"] == "2016/17" for f in r["fixtures"])


def test_an_unplayed_fixture_is_a_different_gap():
    """A fixture still to come is not the same finding as a club being absent,
    so the reason distinguishes them."""
    r = tools.head_to_head("Aston Villa", "Arsenal")
    latest = r["seasons"][1]
    reasons = {g["season"]: g["gap"] for g in r["gaps"]}
    if latest in reasons:
        assert "not been played yet" in reasons[latest]


def test_head_to_head_needs_two_different_clubs():
    assert "error" in tools.head_to_head("Arsenal", "arsenal")
    assert "error" in tools.head_to_head("Arsenal", "Nowhere United")


def test_season_range_narrows_the_fixtures():
    r = tools.head_to_head("Arsenal", "Chelsea", 2015, 2016)
    assert {f["season"] for f in r["fixtures"]} <= {"2015/16", "2016/17"}
    # Two league meetings a season, home and away.
    assert len(r["fixtures"]) == 4
    assert sorted(f["venue"] for f in r["fixtures"]) == [
        "away", "away", "home", "home",
    ]


def test_club_matches_returns_a_full_season():
    r = tools.club_matches("Arsenal", 2003)
    assert r["season"] == "2003/04"
    assert r["record"]["played"] == 38
    # The Invincibles: unbeaten across the whole league season.
    assert r["record"]["lost"] == 0
    assert r["record"]["won"] == 26
    assert r["record"]["drawn"] == 12


def test_club_matches_scores_agree_with_the_result():
    for f in tools.club_matches("Arsenal", 2003)["fixtures"]:
        expected = (
            "W" if f["goals_for"] > f["goals_against"]
            else "D" if f["goals_for"] == f["goals_against"]
            else "L"
        )
        assert f["result"] == expected, f
        assert f["goal_margin"] == f["goals_for"] - f["goals_against"]
        assert f["score"] == f"{f['goals_for']}-{f['goals_against']}"


def test_club_matches_gap_is_a_gap_not_an_empty_season():
    # Luton Town played the Premier League only in 2023/24.
    r = tools.club_matches("Luton Town", 2021)
    assert r["fixtures"] == []
    assert "did not play" in r["gap"]
    assert "record" not in r, "an absent season has no record to report"


def test_club_matches_covers_a_season_in_progress():
    """A season underway returns the matches played so far rather than refusing,
    which is what makes 'up to the present day' answerable."""
    r = tools.club_matches("Arsenal", 2026)
    assert r["record"]["played"] >= 1
    assert len(r["fixtures"]) == r["record"]["played"]


def test_unknown_club_errors_clearly():
    assert "error" in tools.club_matches("Nowhere United", 2020)
