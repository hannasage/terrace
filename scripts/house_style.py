#!/usr/bin/env python3
"""
House style gate.

One canonical definition of the two prose rules from CLAUDE.md, used by both the
Makefile and the ci workflow so local and CI agree. The previous Makefile grep
used a Perl regex, which BSD grep on macOS does not support, so the check
silently passed on the hosts this project actually runs on.

Two rules:
  - No em-dash or en-dash, anywhere, in code or prose.
  - No banned vocabulary in Markdown prose.

Scans tracked files only, so build output and dependencies are never read.
Exits non-zero and lists every offending line if anything is found.

The dash characters are built with chr() below, not written literally, so this
file does not trip the very check it implements. The hook at
.claude/hooks/guardrails.py avoids the same self-reference.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Em-dash (U+2014) and en-dash (U+2013). Built at runtime to keep this source
# ASCII. Checked in every text surface.
DASHES = (chr(0x2014), chr(0x2013))
DASH_SUFFIXES = (".md", ".py", ".sql", ".ts", ".tsx", ".jsx", ".yml", ".yaml")

# Banned vocabulary, checked in Markdown prose only. Code may legitimately use
# some of these words as identifiers. Kept in sync with .github/workflows/ci.yml.
BANNED = (
    "delve", "leverage", "robust", "pivotal", "crucial", "seamless",
    "tapestry", "testament", "underscore", "boasts", "nuanced",
    "multifaceted", "landscape", "realm", "navigate", "foster", "garner",
    "showcase", "intricate", "notably", "moreover", "furthermore",
    "consequently",
)
BANNED_SUFFIXES = (".md",)

BANNED_RE = re.compile(r"\b(" + "|".join(BANNED) + r")\b", re.IGNORECASE)

# Files that state the vocabulary rule have to name the words they ban, so they
# are exempt from the vocabulary check. This is the same self-reference problem
# the dash characters above solve with chr(). The dash check still applies to
# them: quoting a banned word is necessary, writing a dash never is.
BANNED_EXEMPT = frozenset({Path("mcp_server/style/CONTRACT.md")})


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return [Path(line) for line in out.splitlines() if line.strip()]


def main() -> None:
    findings: list[str] = []

    for path in tracked_files():
        if path.suffix not in DASH_SUFFIXES and path.suffix not in BANNED_SUFFIXES:
            continue
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue

        for n, line in enumerate(lines, start=1):
            if path.suffix in DASH_SUFFIXES and any(d in line for d in DASHES):
                findings.append(f"{path}:{n}: em-dash or en-dash")
            if path.suffix in BANNED_SUFFIXES and path not in BANNED_EXEMPT:
                match = BANNED_RE.search(line)
                if match:
                    findings.append(f"{path}:{n}: banned word '{match.group(1)}'")

    if findings:
        print("House style violations:", file=sys.stderr)
        for item in findings:
            print(f"  {item}", file=sys.stderr)
        print(
            "\nSee the conventions in CLAUDE.md. Use commas, colons, or "
            "separate sentences instead of a dash.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("House style clean.")
    sys.exit(0)


if __name__ == "__main__":
    main()
