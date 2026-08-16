# Registry

The single most important set of files in the repository. The application reads
these, never a hardcoded list.

| File | Holds | Who edits |
|---|---|---|
| `metrics.yml` | Every metric the application can plot, one entry each | Hanna approves, Claude may draft |
| `clubs.<nation>.yml` | Canonical clubs for a nation, stable id across renames | Hanna only |
| `people.<nation>.yml` | Canonical players and staff for a nation | Hanna only |
| `aliases.<source>.yml` | Approved name mappings per source | Hanna only, from offline proposals |

Clubs and people are split by nation, not by competition: a club moves between
leagues within a nation through promotion and relegation, so no league owns its
id, while clubs are disjoint across nations. Which competition a club played in
is derived from the data, never the filename. See docs/DECISIONS.md D-012 and
D-002. `clubs.eng.yml` is the first, seeded from engsoccerdata.

Every `clubs.*.yml`, `people.*.yml`, and `aliases.*.yml` is hand-maintained. The
guardrail hook blocks writes to them by prefix. When a source emits an
unrecognised name, the build fails naming the value and the source, and resolving
it is an offline task per docs/DECISIONS.md D-005. The pipeline reads only
committed alias files.
