"""
CLI entry point for ingest.

    python -m pipeline.ingest --sources all --run-date 2026-08-15

--sources is a comma-separated list of source ids, or 'all'. --run-date is the
snapshot date, supplied from outside so nothing here reads the clock; it falls
back to the TERRACE_RUN_DATE environment variable. Writing nothing is a valid,
green outcome: the data-refresh workflow opens a pull request only when a
snapshot actually changed.
"""

from __future__ import annotations

import argparse
import os
import sys

from . import run


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m pipeline.ingest")
    parser.add_argument(
        "--sources",
        default="all",
        help="Comma-separated source ids, or 'all'.",
    )
    parser.add_argument(
        "--run-date",
        default=os.environ.get("TERRACE_RUN_DATE"),
        help="Snapshot date, YYYY-MM-DD. Supplied from outside, never read from "
        "the clock.",
    )
    args = parser.parse_args()

    wrote = run(args.sources, args.run_date)
    print(f"Ingest complete. {wrote} source(s) wrote a new snapshot.")
    sys.exit(0)


if __name__ == "__main__":
    main()
