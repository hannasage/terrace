# Points share

The share of the maximum available points a club took in a season, between 0 and
1.

**Kind:** constructed.

**Formula:** `points / (3 * matches_played)`, rounded to three decimals. Three is
the points available per match. A club winning every game scores 1.0.

**Inputs:** `points` and `matches_played` from `mart__club_season`.

**available_from:** 1992-93.

**Why it matters:** like points per game, it compares fairly across seasons of
different lengths and the in-progress season, but on a fixed 0 to 1 scale.

**Limitations:** the current season is a small-sample rate.
