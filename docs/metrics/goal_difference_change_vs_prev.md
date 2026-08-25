# Goal difference change versus previous season

How a club's goal difference moved from the season before.

**Kind:** constructed. A difference of two seasons' goal differences.

**Formula:** `goal_difference` this season minus `goal_difference` in the season
starting the previous calendar year.

**Inputs:** `goal_difference` from `mart__club_season`, joined to the club's own
previous season.

**available_from:** 1992-93.

**Limitations:** null when the club was not in the league the previous season. Not
carried across a gap. For the current season the value compares a partial total to
a full one, so read it as provisional.
