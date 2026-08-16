#!/usr/bin/env python3
"""
Run the guardrail checks over a diff, in CI.

The local hook at .claude/hooks/guardrails.py only protects sessions that run
the hook. This applies the same checks to every changed file on a pull request,
so the constraints hold on the branch and not only in a local session.

The check functions are imported from the hook rather than duplicated, so there
is one canonical definition of each constraint. When a check fires it calls the
hook's block(), which prints the reason to stderr and raises SystemExit. We
catch that per file, record the failure, and carry on so one run reports every
offending file rather than stopping at the first.

Usage:
    python scripts/guardrails_ci.py <base_sha>

<base_sha> is the commit the branch diverged from. In CI this is
github.event.pull_request.base.sha, with HEAD~1 as a local fallback.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK_DIR = REPO / ".claude" / "hooks"

# Import the single canonical set of check functions from the hook.
sys.path.insert(0, str(HOOK_DIR))
import guardrails  # noqa: E402

# The checks main() runs, in the same order the hook applies them, with one
# deliberate exception. check_registry_not_edited is not run here. In a local
# session it stops Claude from writing the hand-maintained registry. In CI it
# cannot tell Claude's edit from Hanna's, so running it would block the one
# person allowed to change those files from ever committing them. CODEOWNERS
# already routes pipeline/registry/ to Hanna's approval, so a registry edit that
# reaches a pull request is legitimate by construction. The local hook still
# enforces the rule against Claude, where the concern lives. See D-011.
CHECKS = (
    guardrails.check_no_em_dash,
    guardrails.check_source_allowlist,
    guardrails.check_pipeline_determinism,
    guardrails.check_no_export_route,
    guardrails.check_no_commercial,
)


def changed_files(base_sha: str) -> list[str]:
    """Files added, copied, or modified between base_sha and the working tree."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACM", base_sha, "--"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def read_text(path: str) -> str | None:
    """Return the file's text, or None if it is absent or not UTF-8 text."""
    full = REPO / path
    if not full.is_file():
        return None
    try:
        return full.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: guardrails_ci.py <base_sha>")
    base_sha = sys.argv[1]

    files = changed_files(base_sha)
    if not files:
        print("No changed files to check.")
        sys.exit(0)

    blocked: list[str] = []
    for path in files:
        content = read_text(path)
        if content is None:
            continue
        for check in CHECKS:
            try:
                check(path, content)
            except SystemExit:
                # block() has already printed the reason to stderr. Record the
                # file and stop checking it, matching the hook, which blocks the
                # write on the first violation.
                blocked.append(path)
                break

    if blocked:
        print(
            f"\nGuardrails blocked {len(blocked)} file(s): {', '.join(blocked)}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Guardrails clean over {len(files)} changed file(s).")
    sys.exit(0)


if __name__ == "__main__":
    main()
