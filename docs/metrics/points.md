# Points

League points a club earned in a season.

**Kind:** constructed. Points apply a competition rule, not a source value.

**Formula:** `3 * wins + 1 * draws`. The Premier League has used three points for
a win since its 1992 start, so the constant is 3 for every season held here.

**Inputs:** match results (home and away goals) from engsoccerdata and
football-data, aggregated to the club-season grain in `mart__club_season`.

**available_from:** 1992-93, the first season of results.

**Limitations:** the current season is in progress, so its points are a running
total, not a final tally. A season with a points deduction (an administrative
sanction) is not modelled; points here are earned on the pitch only.
