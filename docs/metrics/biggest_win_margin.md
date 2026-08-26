# Biggest win margin

The largest goal margin by which the club won a match that season.

**Kind:** constructed. It is the maximum of a per-match difference, over wins.

**Formula:** `max(goals_for - goals_against)` across the club's won matches,
computed from `mart__club_match`. A win is a match with more goals for than
against.

**Inputs:** match results from engsoccerdata and football-data, at the club-match
grain in `mart__club_match`.

**available_from:** 1992-93.

**Limitations:** null when the club won no match that season, an honest gap rather
than a zero, since there is no winning margin to report. The current season's value
is provisional.
