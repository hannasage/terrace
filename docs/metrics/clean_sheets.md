# Clean sheets

Matches in a season where the club conceded no goal.

**Kind:** constructed. It counts a per-match condition, not a source value.

**Formula:** count of the club's matches with `goals_against = 0`, computed from
`mart__club_match`.

**Inputs:** match results from engsoccerdata and football-data, at the club-match
grain in `mart__club_match`.

**available_from:** 1992-93.

**Limitations:** the current season's count is partial. It says nothing about the
margin of those clean sheets, only that the goal was kept out.
