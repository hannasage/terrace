#!/usr/bin/env python3
"""
Collect the automation metrics required by docs/DECISIONS.md D-008.

The project is half an experiment in how far Claude Code can carry a build with
Hanna only reviewing. Without recorded numbers that experiment produces
anecdote, so these are gathered automatically rather than remembered.

Writes docs/metrics/automation.json.

Usage:
    python scripts/collect_automation_metrics.py --repo hannasage/terrace

Requires GH_TOKEN in the environment with read access to the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("docs/metrics/automation.json")

# Commits from these authors count as human intervention on a branch.
BOT_AUTHORS = {"terrace-bot", "github-actions[bot]", "claude[bot]"}


def gh(path: str, **params) -> list | dict:
    """Call the GitHub API through the gh CLI so auth is handled for us."""
    cmd = ["gh", "api", "--paginate", path]
    for key, value in params.items():
        cmd += ["-f", f"{key}={value}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # --paginate concatenates JSON arrays; normalise to one list.
    chunks = result.stdout.replace("][", ",").strip()
    return json.loads(chunks) if chunks else []


def iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def hours(start: datetime | None, end: datetime | None) -> float | None:
    if not start or not end:
        return None
    return round((end - start).total_seconds() / 3600, 2)


def collect(repo: str) -> dict:
    prs = gh(f"repos/{repo}/pulls", state="closed", per_page="100")
    merged = [p for p in prs if p.get("merged_at")]

    autonomous = 0
    human_touched = 0
    intervention_counts: list[int] = []
    lead_times: list[float] = []
    by_lane: Counter = Counter()

    for pr in merged:
        number = pr["number"]
        labels = {label["name"] for label in pr.get("labels", [])}
        lane = "data" if "data" in labels else "code"
        by_lane[lane] += 1

        commits = gh(f"repos/{repo}/pulls/{number}/commits")
        reviews = gh(f"repos/{repo}/pulls/{number}/reviews")
        comments = gh(f"repos/{repo}/pulls/{number}/comments")

        human_commits = sum(
            1
            for c in commits
            if (c.get("author") or {}).get("login") not in BOT_AUTHORS
            and (c.get("author") or {}).get("login") is not None
        )

        # An intervention is any point where a human had to act on the branch:
        # a commit of their own, a review, or a line comment. Approvals with no
        # commentary on a clean pull request are counted, since reading it was
        # still work.
        interventions = human_commits + len(reviews) + len(comments)
        intervention_counts.append(interventions)

        if human_commits == 0:
            autonomous += 1
        else:
            human_touched += 1

        lead = hours(iso(pr.get("created_at")), iso(pr.get("merged_at")))
        if lead is not None:
            lead_times.append(lead)

    # Failed required checks, so the noisy assertion becomes visible rather
    # than merely annoying.
    runs = gh(f"repos/{repo}/actions/runs", status="failure", per_page="100")
    failures: Counter = Counter()
    if isinstance(runs, dict):
        runs = runs.get("workflow_runs", [])
    for run in runs:
        failures[run.get("name", "unknown")] += 1

    total = len(merged)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "merged_pull_requests": total,
        "authored_end_to_end_by_claude": autonomous,
        "share_authored_end_to_end": round(autonomous / total, 3) if total else None,
        "human_touched": human_touched,
        "interventions_per_pr_mean": (
            round(sum(intervention_counts) / len(intervention_counts), 2)
            if intervention_counts
            else None
        ),
        "lead_time_hours_median": (
            round(sorted(lead_times)[len(lead_times) // 2], 2) if lead_times else None
        ),
        "merged_by_lane": dict(by_lane),
        "failed_workflow_runs_by_name": dict(failures),
        "guardrail_blocks_by_rule": read_guardrail_log(),
        "notes": (
            "guardrail_blocks_by_rule is the number that decides whether a "
            "constraint belongs in a hook or in prose. A rule that never fires "
            "was never needed. A rule that fires constantly is either wrong or "
            "badly explained."
        ),
    }


def read_guardrail_log() -> dict:
    """Guardrail blocks are appended locally by the hook. Absent in CI."""
    log = Path(".claude/hooks/blocks.log")
    if not log.exists():
        return {}
    counts: dict[str, int] = defaultdict(int)
    for line in log.read_text().splitlines():
        if line.startswith("BLOCKED ["):
            rule = line.split("[", 1)[1].split("]", 1)[0]
            counts[rule] += 1
    return dict(counts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    args = parser.parse_args()

    if not os.environ.get("GH_TOKEN"):
        raise SystemExit("GH_TOKEN is not set.")

    data = collect(args.repo)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
