# Champion

Whether a club won the league that season. A 0 or 1 flag.

**Kind:** constructed. It reads off the final standing.

**Formula:** 1 when `league_position` is 1 at season end, 0 otherwise.

**Inputs:** `league_position` from `mart__club_season`.

**available_from:** 1992-93.

**Limitations:** the value is null for the current season, because the title is
undetermined while the season is in progress. It is not a premature flag on
whoever is top today. It reflects on-pitch results only, not any administrative
sanction.
