# Points per game

Average league points a club earned per match in a season.

**Kind:** constructed. It divides one constructed metric by a count.

**Formula:** `points / matches_played`, rounded to two decimals.

**Inputs:** `points` and `matches_played` from `mart__club_season`.

**available_from:** 1992-93.

**Why it matters:** it is the fair way to compare across seasons of different
lengths, the 42-match seasons of 1992/93 to 1994/95, the 38-match seasons since,
and the in-progress current season, which total points cannot compare honestly.

**Limitations:** for the current season the value is a small-sample rate and will
move as more matches are played.
