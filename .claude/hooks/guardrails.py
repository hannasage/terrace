#!/usr/bin/env python3
"""
Blocking guardrails for Terrace.

Wired as a PreToolUse hook on file-writing tools. Reads the hook payload from
stdin, inspects the proposed path and content, and exits non-zero to block.

These checks exist because CLAUDE.md is context, not enforcement. Anything that
must never happen is checked here rather than described in prose.

VERIFY BEFORE RELYING ON THIS: the hook payload schema and the blocking exit
code are Claude Code implementation details and change between versions. Check
the current hooks reference at https://code.claude.com/docs/en/ and adjust
`read_payload` and `BLOCK_EXIT` to match. The checks themselves are the durable
part.
"""

import json
import re
import sys
from pathlib import Path

BLOCK_EXIT = 2

REPO = Path(__file__).resolve().parents[2]


def read_payload():
    """Extract (path, content) from the hook payload.

    Fails closed. An unreadable payload means the checks below cannot run, and
    an unchecked write is exactly what this hook exists to prevent. The only
    case that passes through is genuinely empty stdin, which means the hook was
    invoked outside a tool call.
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return None, None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        block(
            "unreadable-payload",
            f"could not parse the hook payload ({exc}). Blocking rather than "
            "allowing an unchecked write. If the Claude Code payload schema "
            "has changed, update read_payload in this file.",
        )
    params = payload.get("tool_input") or payload.get("parameters") or {}
    path = params.get("file_path") or params.get("path") or ""
    content = (
        params.get("content")
        or params.get("file_text")
        or params.get("new_str")
        or ""
    )
    return path, content


def block(rule, detail):
    print(f"BLOCKED [{rule}] {detail}", file=sys.stderr)
    print(
        "This constraint is in SPEC.md section 3. If you believe it is wrong, "
        "stop and raise it with Hanna rather than working around it.",
        file=sys.stderr,
    )
    sys.exit(BLOCK_EXIT)


def is_prose(path):
    """Documentation may name what code may not do.

    Without this, the register that lists the excluded sources cannot be
    written, because it contains their hostnames, and the hook cannot edit
    itself, because it contains the patterns it blocks. The content checks
    below exist to stop the pipeline fetching from an excluded source and to
    keep commercial code out of the application. Neither risk exists in prose.
    """
    return (
        path.startswith("docs/")
        or path.startswith(".claude/")
        or path.startswith(".github/")
        or ("/" not in path and path.endswith(".md"))
    )


# --- checks -----------------------------------------------------------------


def check_no_export_route(path, content):
    """Principle 3: the product presents data, it does not hand it back out."""
    if not path.startswith("web/"):
        return
    api_route = re.search(r"web/app/api/(?!og/)", path)
    if api_route:
        block(
            "no-api",
            f"{path} creates an API route. The only permitted dynamic route is "
            "web/app/api/og/ for preview images.",
        )
    export_markers = [
        r"text/csv",
        r"application/vnd\.ms-excel",
        r"Content-Disposition",
        r"download\s*=",
        r"toBlob\s*\(",
        r"createObjectURL",
        r"\bexportToCsv\b",
        r"\bdownloadData\b",
    ]
    for marker in export_markers:
        if re.search(marker, content):
            block("no-export", f"{path} contains an export affordance: {marker}")


def check_no_commercial(path, content):
    """Principle 2: nothing commercial in the shipped application."""
    if is_prose(path):
        return
    markers = [
        r"googletagmanager",
        r"google-analytics",
        r"gtag\(",
        r"adsbygoogle",
        r"\bstripe\b",
        r"\bpaddle\.js\b",
        r"affiliate",
        r"\bbet365\b",
        r"utm_campaign",
    ]
    for marker in markers:
        if re.search(marker, content, re.IGNORECASE):
            block("no-commercial", f"{path} contains a commercial marker: {marker}")


def check_source_allowlist(path, content):
    """Principle 1: registered sources only, and never the excluded ones."""
    excluded = {
        "fbref.com": "excluded, see docs/DATA-SOURCES.md",
        "stathead.com": "excluded, see docs/DATA-SOURCES.md",
        "sports-reference.com": "excluded, see docs/DATA-SOURCES.md",
        "premierleague.com/en/": "site scraping excluded, use the fantasy API",
    }
    if not is_prose(path):
        for host, why in excluded.items():
            if host in content:
                block("excluded-source", f"{path} references {host}. {why}")

    if not path.startswith("pipeline/ingest/"):
        return
    registered = [
        "football-data.co.uk",
        "understat.com",
        "fantasy.premierleague.com",
        "api.clubelo.com",
        "raw.githubusercontent.com/jalapic/engsoccerdata",
    ]
    hosts = re.findall(r"https?://([^/\s\"']+)", content)
    for host in hosts:
        if not any(host in reg or reg.startswith(host) for reg in registered):
            block(
                "unregistered-source",
                f"{path} fetches from {host}, which has no entry in "
                "docs/DATA-SOURCES.md. Propose it in DECISIONS.md and stop.",
            )


def check_pipeline_determinism(path, content):
    """Principle 9: nothing non-deterministic in the transformation path."""
    if not path.startswith("pipeline/"):
        return
    markers = {
        r"anthropic": "no model API call inside pipeline/",
        r"\bopenai\b": "no model API call inside pipeline/",
        r"\bfuzzywuzzy\b": "no fuzzy matching, use the alias registry",
        r"\brapidfuzz\b": "no fuzzy matching, use the alias registry",
        r"difflib\.get_close_matches": "no fuzzy matching, use the alias registry",
        r"\.interpolate\(": "no interpolation, gaps stay as gaps",
        r"\.fillna\(": "no gap filling, gaps stay as gaps",
        r"\bffill\b": "no gap filling, gaps stay as gaps",
        r"random\.": "no randomness in the pipeline",
        r"datetime\.now\(\)": "no wall-clock dependency, pass the run date in",
    }
    for marker, why in markers.items():
        if re.search(marker, content, re.IGNORECASE):
            block("determinism", f"{path}: {why} (matched {marker})")


def check_registry_not_edited(path, _content):
    """Hand-maintained registries are Hanna's, not Claude's."""
    protected = (
        "pipeline/registry/clubs.yml",
        "pipeline/registry/people.yml",
        "pipeline/registry/aliases.",
    )
    if any(path.startswith(p) for p in protected):
        block(
            "protected-registry",
            f"{path} is hand-maintained. Report the unresolved value and stop.",
        )


def check_no_em_dash(path, content):
    """House style, everywhere, no exceptions."""
    if "\u2014" in content or "\u2013" in content:
        block("em-dash", f"{path} contains an em-dash or en-dash.")


def main():
    path, content = read_payload()
    if not path:
        sys.exit(0)
    path = path.replace(str(REPO) + "/", "")

    check_no_em_dash(path, content)
    check_registry_not_edited(path, content)
    check_source_allowlist(path, content)
    check_pipeline_determinism(path, content)
    check_no_export_route(path, content)
    check_no_commercial(path, content)
    sys.exit(0)


if __name__ == "__main__":
    main()
