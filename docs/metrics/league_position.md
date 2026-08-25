# League position

Where a club finished in the table at the end of a season. 1 is champions.

**Kind:** constructed. It ranks clubs within a season by a competition rule.

**Formula:** rank within the season ordered by points descending, then goal
difference descending, then goals scored descending. This is the Premier League's
tie-break order. Head-to-head record, which the Premier League uses only in the
rare case that those three are all equal, is not modelled, so a position may
differ from the official table in that uncommon case.

**Inputs:** `points`, `goal_difference`, `goals_for` from `mart__club_season`.

**available_from:** 1992-93.

**higher_is_better:** false. A lower number is a better finish.

**Limitations:** the current season is in progress, so its positions are a live
snapshot, not a final standing. Positions here reflect on-pitch results only, not
any administrative points deduction.
