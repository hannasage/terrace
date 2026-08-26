"""
Report style and theme tools.

The data tools in terrace_tools.py answer what the numbers are. These answer how
a report presenting them should look. They are deterministic file reads plus
contrast arithmetic, no model call and no network, so the same rules apply: the
tools compute, the agent narrates.

Three things live here:

  - the house format contract and the copyable JSX skeleton, read from style/
  - the theme registry, vendored verbatim from the resume repository by
    scripts/vendor_themes.py, never invented here
  - WCAG contrast computed per theme, so the accessibility floor in the contract
    is a number this module derives rather than a claim someone eyeballed

Two themes ship by default, one dark and one light, because the working paper
format carries a two theme switcher. Every other theme is opt in: the reader asks
for it by name. A name that does not exist comes back as an error listing the
valid ids, never as a silent fall back to the default, because quietly rendering
the wrong palette is the kind of failure this project treats as loud.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

STYLE_DIR = Path(__file__).resolve().parent / "style"
THEMES_JSON = STYLE_DIR / "themes.json"
CONTRACT_MD = STYLE_DIR / "CONTRACT.md"
TEMPLATE_JSX = STYLE_DIR / "template.jsx"

# WCAG 2.2 thresholds. The contract asks for 4.5:1 as the floor, 7.0:1 for body
# copy, and 3.0:1 for gridlines and other essential graphical objects.
AA_BODY = 7.0
AA_TEXT = 4.5
AA_NONTEXT = 3.0


def _style_override() -> str | None:
    """The user's own contract, when TERRACE_STYLE_FILE names one.

    A path that is set but unreadable raises rather than falling back to the
    default. Someone who pointed the server at a style file wants that file, and
    silently serving a different one would be the wrong answer delivered quietly.
    """
    raw = os.environ.get("TERRACE_STYLE_FILE", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(
            f"TERRACE_STYLE_FILE is set to {path}, which cannot be read: {exc}"
        ) from exc


def _relative_luminance(hex_colour: str) -> float:
    """Relative luminance of a #rrggbb colour, per the WCAG definition."""
    value = hex_colour.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    """Contrast ratio between two colours, from 1.0 to 21.0."""
    la, lb = _relative_luminance(a), _relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _load() -> dict:
    """The vendored theme registry."""
    return json.loads(THEMES_JSON.read_text(encoding="utf-8"))


def _signature(theme: dict) -> str:
    """A palette fingerprint, used to fold duplicate themes onto one canonical id.

    The registry carries alias entries that repeat an existing palette under a
    second name. Detecting them by their colours rather than by a hardcoded list
    means a new alias upstream folds itself without an edit here.
    """
    plan = "".join(p["value"] for p in theme["planColors"])
    return json.dumps(theme["colors"], sort_keys=True) + plan


def _canonical(themes: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Split the registry into canonical themes and an alias id to canonical id map."""
    seen: dict[str, str] = {}
    canonical: list[dict] = []
    aliases: dict[str, str] = {}
    for theme in themes:
        sig = _signature(theme)
        if sig in seen:
            aliases[theme["id"]] = seen[sig]
        else:
            seen[sig] = theme["id"]
            canonical.append(theme)
    return canonical, aliases


def _contrast_facts(colours: dict) -> dict:
    """The contrast numbers that decide how a theme may be used.

    accent is the one that varies. In some light themes it sits below the text
    floor against its own background, so it is a graphical colour there and must
    not carry words. The report says so rather than letting the agent guess.
    """
    text_on_bg = contrast(colours["text"], colours["bg"])
    text_on_surface = contrast(colours["text"], colours["surface"])
    muted_on_bg = contrast(colours["muted"], colours["bg"])
    accent_on_bg = contrast(colours["accent"], colours["bg"])
    text_on_accent = contrast(colours["textOnAccent"], colours["accent"])
    return {
        "text_on_bg": round(text_on_bg, 2),
        "text_on_surface": round(text_on_surface, 2),
        "muted_on_bg": round(muted_on_bg, 2),
        "accent_on_bg": round(accent_on_bg, 2),
        "text_on_accent": round(text_on_accent, 2),
        "accent_safe_for_text": accent_on_bg >= AA_TEXT,
        "accent_safe_for_graphics": accent_on_bg >= AA_NONTEXT,
        "accent_safe_for_labels": text_on_accent >= AA_TEXT,
    }


def _describe(theme: dict, registry: dict) -> dict:
    """One theme as the tools present it: identity, swatches, contrast facts."""
    colours = theme["colors"]
    return {
        "id": theme["id"],
        "name": theme["name"],
        "mode": "dark" if theme["isDark"] else "light",
        "is_default": theme["id"]
        in (registry["default_dark"], registry["default_light"]),
        "swatches": {
            "bg": colours["bg"],
            "surface": colours["surface"],
            "text": colours["text"],
            "accent": colours["accent"],
        },
        "contrast": _contrast_facts(colours),
    }


def list_themes() -> dict:
    """Every report theme, with the core colours and the contrast facts."""
    registry = _load()
    canonical, aliases = _canonical(registry["themes"])
    described = [_describe(t, registry) for t in canonical]
    return {
        "themes": described,
        "default_dark": registry["default_dark"],
        "default_light": registry["default_light"],
        "aliases": aliases,
        "source": registry["source"],
        "note": (
            "A report ships with the two defaults, one dark and one light. "
            "Any other theme is opt in: name it to use it."
        ),
    }


def _resolve(theme_id: str | None, registry: dict) -> tuple[dict, dict] | dict:
    """The dark and light pair a report ships with.

    Naming a theme replaces the slot matching its own mode, so asking for a light
    theme keeps the default dark one alongside it and the switcher still works.
    """
    canonical, aliases = _canonical(registry["themes"])
    by_id = {t["id"]: t for t in canonical}

    dark = by_id[registry["default_dark"]]
    light = by_id[registry["default_light"]]

    if theme_id:
        wanted = aliases.get(theme_id, theme_id)
        if wanted not in by_id:
            return {
                "error": (
                    f"Unknown theme '{theme_id}'. Call list_themes for the set. "
                    f"Valid ids: {', '.join(sorted(by_id))}."
                )
            }
        chosen = by_id[wanted]
        if chosen["isDark"]:
            dark = chosen
        else:
            light = chosen

    return dark, light


def _theme_payload(theme: dict) -> dict:
    """A theme in full, ready to paste into the template's token block."""
    return {
        "id": theme["id"],
        "name": theme["name"],
        "mode": "dark" if theme["isDark"] else "light",
        "colors": theme["colors"],
        "planColors": theme["planColors"],
        "contrast": _contrast_facts(theme["colors"]),
    }


def report_style(theme: str | None = None) -> dict:
    """The house format for a Terrace report artifact.

    Returns the contract, the copyable skeleton, and the resolved dark and light
    theme pair. theme names one palette to swap into its own slot; omit it for
    the shipped defaults.
    """
    registry = _load()
    resolved = _resolve(theme, registry)
    if isinstance(resolved, dict):
        return resolved
    dark, light = resolved

    override = _style_override()
    return {
        "contract": override or CONTRACT_MD.read_text(encoding="utf-8"),
        "source": "override" if override else "default",
        "template": TEMPLATE_JSX.read_text(encoding="utf-8"),
        "themes": {"dark": _theme_payload(dark), "light": _theme_payload(light)},
        "thresholds": {
            "body_copy": AA_BODY,
            "text": AA_TEXT,
            "non_text": AA_NONTEXT,
        },
    }
