# Registry

The single most important set of files in the repository. The application reads
these, never a hardcoded list.

| File | Holds | Who edits |
|---|---|---|
| `metrics.yml` | Every metric the application can plot, one entry each | Hanna approves, Claude may draft |
| `clubs.yml` | Canonical club list, stable id across renames | Hanna only |
| `people.yml` | Canonical player and staff list | Hanna only |
| `aliases.<source>.yml` | Approved name mappings per source | Hanna only, from offline proposals |

`clubs.yml`, `people.yml`, and every `aliases.*.yml` are hand-maintained. The
guardrail hook blocks writes to them. When a source emits an unrecognised name,
the build fails naming the value and the source, and resolving it is an offline
task per docs/DECISIONS.md D-005. The pipeline reads only committed alias files.

These files do not exist yet. Seeding `clubs.yml` is a Hanna step, per
BOOTSTRAP.md Phase 4.
