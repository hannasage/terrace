# Win rate

Share of a club's matches in a season that it won.

**Kind:** constructed. A ratio of a count to a count.

**Formula:** `wins / matches_played`, rounded to three decimals, between 0 and 1.

**Inputs:** `wins` and `matches_played` from `mart__club_season`.

**available_from:** 1992-93.

**Limitations:** it ignores draws, so two clubs with the same win rate can have
very different points. Read it alongside points per game, not instead of it. The
current season's value is a small-sample rate.
