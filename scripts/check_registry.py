#!/usr/bin/env python3
"""
Registry consistency gate.

Stub. Exits zero so the pipeline CI job is wired end to end before the marts
exist. Fill in when the dbt marts and pipeline/registry/metrics.yml are real.

TODO, the registry-coverage gate from SPEC.md section 4.6:
  - Every mart column maps to exactly one entry in pipeline/registry/metrics.yml.
  - Every registry entry maps to a real mart column.
  - Every entry's definition_url points at a docs/metrics/ file that exists.
  - kind is observed or constructed, and a derived ratio is constructed.
  - available_from is a season string the dbt models actually honour.
Fail closed: any mismatch exits non-zero and names the offending id or column.
"""

import sys


def main() -> None:
    print("check_registry.py: stub, nothing to assert yet. Exiting 0.")
    sys.exit(0)


if __name__ == "__main__":
    main()
