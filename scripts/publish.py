#!/usr/bin/env python3
"""
Publish Parquet artefacts to web/public/data.

Stub. Exits zero so the pipeline CI job and the data-refresh workflow are wired
end to end before the marts exist. Fill in when the dbt marts are real.

--check runs the assertions without writing, for use as a CI gate. Without it
the artefacts are written, for use in the data-refresh workflow.

TODO:
  - Read the built dbt marts from the DuckDB database.
  - Write one Parquet file per published mart into web/public/data, laid out for
    DuckDB-WASM HTTP range requests (see docs/DECISIONS.md D-006).
  - In --check mode, assert the artefacts on disk match what a fresh build would
    produce, and exit non-zero on any drift.
  - Never write an export route or a bulk endpoint. Static files only.
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Assert artefacts are current without writing them.",
    )
    args = parser.parse_args()

    mode = "check" if args.check else "write"
    print(f"publish.py: stub ({mode} mode), no marts to publish yet. Exiting 0.")
    sys.exit(0)


if __name__ == "__main__":
    main()
