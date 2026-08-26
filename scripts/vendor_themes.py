#!/usr/bin/env python3
"""
Vendor the report theme registry.

Reads app/lib/projection-themes.ts from the hannasage/resume repository and
writes mcp_server/style/themes.json. The palettes are copied, never invented or
retyped, which is the rule FORMAT-STANDARD states and the reason this is a script
rather than a hand-written file: 14 themes times 23 colour values is too much to
transcribe reliably.

    python scripts/vendor_themes.py ../resume/app/lib/projection-themes.ts

Re-run it when the upstream palette changes. The written file records the source
path and the commit it was taken from, so a stated colour always names its source.

Determinism: reads a file, writes a file, no network and no clock beyond the git
commit it reads from the source repository.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "mcp_server" / "style" / "themes.json"

# The two themes the report ships with. Everything else is opt in, chosen by the
# reader by name. Recorded here so one place decides the shipped pair.
DEFAULT_DARK = "projection"
DEFAULT_LIGHT = "coastal-day"


def source_commit(path: Path) -> str:
    """The commit of the repository the source file lives in, or 'unknown'."""
    try:
        out = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def parse_themes(text: str) -> list[dict]:
    """The THEMES array from the TypeScript source, as plain data.

    The source is a plain object literal with no computed values, so it converts
    to JSON by quoting the keys, swapping quote characters and dropping trailing
    commas. Anything that does not convert cleanly raises, because a silently
    half-parsed palette would be worse than no palette.
    """
    start = text.find("export const THEMES")
    if start == -1:
        raise SystemExit("No 'export const THEMES' in the source file.")
    # Anchor on the assignment, not the first bracket: the type annotation
    # 'Theme[]' carries a bracket that would otherwise match first.
    open_at = text.index("= [", start) + 2
    body = text[open_at : text.index("\n];", start) + 2]

    body = re.sub(r"//[^\n]*", "", body)          # line comments
    body = re.sub(r"(\w+)\s*:", r'"\1":', body)   # bare keys to quoted keys
    body = body.replace("'", '"')                 # single to double quotes
    body = re.sub(r",(\s*[}\]])", r"\1", body)    # trailing commas

    try:
        themes = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse the THEMES array: {exc}") from exc

    if not themes:
        raise SystemExit("The THEMES array parsed as empty.")
    return themes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source", type=Path, help="Path to projection-themes.ts in the resume repo."
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"No such file: {args.source}")

    src = args.source.resolve()
    themes = parse_themes(src.read_text(encoding="utf-8"))

    ids = [t["id"] for t in themes]
    for want in (DEFAULT_DARK, DEFAULT_LIGHT):
        if want not in ids:
            raise SystemExit(f"The source has no theme with id '{want}'.")

    payload = {
        "source": {
            "repository": "hannasage/resume",
            "path": "app/lib/projection-themes.ts",
            "commit": source_commit(src),
        },
        "default_dark": DEFAULT_DARK,
        "default_light": DEFAULT_LIGHT,
        "themes": themes,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(themes)} themes to {OUT.relative_to(REPO)}.")
    sys.exit(0)


if __name__ == "__main__":
    main()
