"""
Tests for the server instructions.

The instructions are the only guidance every conversation receives, so the things
checked here are the things that would silently stop happening: the three reading
levels, the prose budget, the honesty rules, and the pointer to report_style.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guidance  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_mode(monkeypatch):
    monkeypatch.delenv("TERRACE_DEFAULT_MODE", raising=False)


def test_every_mode_is_described():
    text = guidance.build_instructions()
    for mode in ("learning", "exploration", "analytics"):
        assert mode in text
    assert guidance.MODES == ("learning", "exploration", "analytics")


def test_unset_mode_asks_once():
    text = guidance.build_instructions()
    assert guidance.default_mode() is None
    assert "ask once" in text.lower()


def test_pinned_mode_suppresses_the_question(monkeypatch):
    monkeypatch.setenv("TERRACE_DEFAULT_MODE", "Analytics")
    assert guidance.default_mode() == "analytics"
    text = guidance.build_instructions()
    assert "Do not ask" in text


def test_unknown_mode_fails_loudly(monkeypatch):
    monkeypatch.setenv("TERRACE_DEFAULT_MODE", "expert")
    with pytest.raises(SystemExit) as exc:
        guidance.default_mode()
    # The message has to name the valid set, or the fix is guesswork.
    for mode in guidance.MODES:
        assert mode in str(exc.value)


def test_prose_economy_is_stated():
    text = guidance.build_instructions().lower()
    assert "never restate" in text
    assert "never narrate" in text


def test_honesty_rules_survive_in_the_instructions():
    text = guidance.build_instructions().lower()
    assert "constructed" in text
    assert "never a zero" in text
    assert "sources" in text


def test_report_style_is_pointed_at():
    assert "report_style" in guidance.build_instructions()


def test_instructions_carry_no_dashes():
    # The house rule, checked here because these strings reach the user.
    text = guidance.build_instructions()
    assert chr(0x2014) not in text
    assert chr(0x2013) not in text


def test_presentation_requires_an_artifact_for_a_report():
    """More than one figure is a report. This rides on every tool result because
    a client may ignore the server instructions, and one did."""
    p = guidance.presentation(values=12)
    assert p["output"] == "artifact"
    assert "report_style" in p["before_rendering"]
    assert "line or two" in p["chat_reply"]


def test_presentation_leaves_a_single_figure_in_chat():
    p = guidance.presentation(values=1)
    assert p["output"].startswith("chat")
    assert "before_rendering" not in p


def test_presentation_marks_a_catalogue_as_not_an_answer():
    p = guidance.presentation(None)
    assert p["output"].startswith("chat")
    assert "catalogue" in p["output"]


def test_presentation_carries_the_prose_rule_and_mode(monkeypatch):
    assert "restate" in guidance.presentation(values=3)["prose"]
    monkeypatch.setenv("TERRACE_DEFAULT_MODE", "analytics")
    assert guidance.presentation(values=3)["reading_level"] == "analytics"


def test_presentation_says_to_ask_when_no_mode_is_pinned():
    assert "ask" in guidance.presentation(values=3)["reading_level"]


def test_instructions_stay_short():
    # They are sent on every conversation. Growth here is a cost on every turn,
    # which is why the long format contract lives behind report_style instead.
    assert len(guidance.build_instructions()) < 6000
