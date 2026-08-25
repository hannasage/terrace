# Goal difference

Goals scored minus goals conceded across a club's season.

**Kind:** constructed. It is derived from two observed totals.

**Formula:** `goals_for - goals_against`.

**Inputs:** match results from engsoccerdata and football-data, aggregated in
`mart__club_season`.

**available_from:** 1992-93.

**Limitations:** the current season's value is a running total. Goal difference
is the Premier League's first tie-breaker on points, but the ordering itself is
not modelled here, only the quantity.
