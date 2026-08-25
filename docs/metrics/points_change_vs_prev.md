# Points change versus previous season

How many more or fewer points a club earned than in the season before.

**Kind:** constructed. A difference of two seasons' points.

**Formula:** `points` this season minus `points` in the season starting the
previous calendar year.

**Inputs:** `points` from `mart__club_season`, joined to the club's own previous
season.

**available_from:** 1992-93.

**Limitations:** null when the club was not in the league the previous season, so
a promoted club has no change in its first season back. It is not carried across a
gap: a club relegated then promoted is compared to the season immediately before,
which is null, not to its last top-flight season. For the current season the value
compares a partial total to a full one, so read it as provisional.
