# Relegated

Whether a club was relegated from the league that season. A 0 or 1 flag.

**Kind:** constructed. It applies the competition's relegation rule to the final
standing.

**Formula:** 1 when the club finished in a relegation place, 0 otherwise. The
relegation places are the bottom three, except the bottom four at the end of
1994/95, when the Premier League cut from 22 clubs to 20.

**Inputs:** `league_position` and the club count per season from
`mart__club_season`.

**available_from:** 1992-93.

**Limitations:** the value is null for the current season, because relegation is
undetermined while the season is in progress. It reflects on-pitch results only,
not any administrative sanction or expulsion.
