"""
Tests for the report style and theme tools.

Two things are being protected. The style contract has to arrive intact and be
overridable by the reader, and the themes have to be the vendored palettes with
honest contrast attached, because the contract tells the agent to trust those
numbers when deciding what may carry text.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import style_tools as style  # noqa: E402

COLOUR_KEYS = {
    "bg", "surface", "faint", "border", "text", "muted", "accent", "dim",
    "blue", "orange", "red", "purple", "textOnAccent",
}


@pytest.fixture(autouse=True)
def _clear_override(monkeypatch):
    monkeypatch.delenv("TERRACE_STYLE_FILE", raising=False)


# ------------------------------------------------------------------ contract


def test_report_style_returns_contract_and_template():
    r = style.report_style()
    assert r["source"] == "default"
    assert "Terrace report format" in r["contract"]
    assert "export default function App" in r["template"]


def test_override_replaces_the_contract(monkeypatch, tmp_path):
    mine = tmp_path / "style.md"
    mine.write_text("# My format\n\nOne page, no charts.\n", encoding="utf-8")
    monkeypatch.setenv("TERRACE_STYLE_FILE", str(mine))
    r = style.report_style()
    assert r["source"] == "override"
    assert r["contract"] == mine.read_text(encoding="utf-8")
    # The skeleton still ships: an override of the prose is not an override of
    # the shell the artifact needs to run.
    assert "export default function App" in r["template"]


def test_unreadable_override_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.setenv("TERRACE_STYLE_FILE", str(tmp_path / "absent.md"))
    with pytest.raises(SystemExit) as exc:
        style.report_style()
    assert "cannot be read" in str(exc.value)


def test_contract_and_template_carry_no_dashes():
    r = style.report_style()
    for name in ("contract", "template"):
        assert chr(0x2014) not in r[name], name
        assert chr(0x2013) not in r[name], name


def test_template_is_artifact_safe():
    """Only React. The artifact sandbox installs nothing, so an import of a chart
    library would be a report that never renders."""
    text = style.TEMPLATE_JSX.read_text(encoding="utf-8")
    # Match the module specifier, not the line, since the import list wraps.
    modules = set(re.findall(r"""\bfrom\s+["']([^"']+)["']""", text))
    assert modules == {"react"}, modules


def test_template_never_fills_a_gap_with_zero():
    text = style.TEMPLATE_JSX.read_text(encoding="utf-8")
    assert "No figure" in text
    assert "segments" in text, "a gap has to break the line, not interpolate"


# -------------------------------------------------------------------- themes


def test_every_theme_is_complete():
    registry = json.loads(style.THEMES_JSON.read_text(encoding="utf-8"))
    assert registry["source"]["path"].endswith("projection-themes.ts")
    for theme in registry["themes"]:
        assert set(theme["colors"]) == COLOUR_KEYS, theme["id"]
        assert len(theme["planColors"]) == 10, theme["id"]


def test_aliases_fold_onto_their_palette():
    listing = style.list_themes()
    ids = {t["id"] for t in listing["themes"]}
    # party repeats projection's palette, so it is not offered as a second look.
    assert listing["aliases"] == {"party": "projection", "party-light": "coastal-day"}
    assert "party" not in ids
    assert listing["default_dark"] in ids
    assert listing["default_light"] in ids


def test_exactly_one_default_per_mode():
    listing = style.list_themes()
    defaults = [t for t in listing["themes"] if t["is_default"]]
    assert sorted(t["mode"] for t in defaults) == ["dark", "light"]


def test_listing_shows_core_colours():
    for theme in style.list_themes()["themes"]:
        assert set(theme["swatches"]) == {"bg", "surface", "text", "accent"}
        assert all(v.startswith("#") for v in theme["swatches"].values())


def test_named_theme_replaces_its_own_slot():
    dark = style.report_style("ember-tide")["themes"]
    assert dark["dark"]["id"] == "ember-tide"
    assert dark["light"]["id"] == "coastal-day"

    light = style.report_style("fernwood")["themes"]
    assert light["dark"]["id"] == "projection"
    assert light["light"]["id"] == "fernwood"


def test_alias_resolves_to_its_canonical_theme():
    assert style.report_style("party")["themes"]["dark"]["id"] == "projection"


def test_unknown_theme_names_the_valid_ids():
    r = style.report_style("midnight-reff")
    assert "error" in r
    assert "midnight-reef" in r["error"]


# ------------------------------------------------------------------ contrast


def test_contrast_matches_the_wcag_worked_example():
    # Black on white is 21:1 exactly, the top of the scale.
    assert round(style.contrast("#000000", "#ffffff"), 2) == 21.0
    assert round(style.contrast("#ffffff", "#ffffff"), 2) == 1.0


def test_body_text_clears_the_body_floor_in_every_theme():
    for theme in style.list_themes()["themes"]:
        c = theme["contrast"]
        assert c["text_on_bg"] >= style.AA_BODY, theme["id"]
        assert c["text_on_surface"] >= style.AA_BODY, theme["id"]


def test_muted_text_clears_the_text_floor_in_every_theme():
    for theme in style.list_themes()["themes"]:
        assert theme["contrast"]["muted_on_bg"] >= style.AA_TEXT, theme["id"]


def test_accent_safety_is_reported_not_assumed():
    """Some light themes have an accent below the text floor against their own
    background. The tools say so per theme rather than letting the agent guess,
    and the contract tells it to read this before setting words in accent."""
    themes = {t["id"]: t["contrast"] for t in style.list_themes()["themes"]}

    assert themes["projection"]["accent_safe_for_text"] is True
    # Verified against the vendored palette: fernwood is 2.97 and
    # dust-and-flame is 2.64 against their own backgrounds.
    assert themes["fernwood"]["accent_safe_for_text"] is False
    assert themes["dust-and-flame"]["accent_safe_for_text"] is False

    for theme_id, c in themes.items():
        assert c["accent_safe_for_text"] == (c["accent_on_bg"] >= style.AA_TEXT)
        assert c["accent_safe_for_graphics"] == (c["accent_on_bg"] >= style.AA_NONTEXT)
