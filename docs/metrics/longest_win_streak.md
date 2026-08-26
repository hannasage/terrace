# Longest win streak

The most consecutive wins the club managed in a season.

**Kind:** constructed. It counts the longest unbroken run of wins in match order.

**Formula:** over the club's matches ordered within the season by date (then match
id as a stable tie-break), the longest run of consecutive `W` results, computed
from `mart__club_match` with a gaps-and-islands aggregation. A club that won no
match has a streak of 0.

**Inputs:** match results and dates from engsoccerdata and football-data, at the
club-match grain in `mart__club_match`.

**available_from:** 1992-93.

**Limitations:** the run depends on a reliable match order, so it depends on the
match date. `assert_match_date_present` guarantees no Premier League match has a
null date, keeping the order total. The current season's value is provisional.
