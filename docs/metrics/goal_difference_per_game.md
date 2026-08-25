# Goal difference per game

Average net goals a club managed per match in a season.

**Kind:** constructed. A signed count divided by a count.

**Formula:** `goal_difference / matches_played`, rounded to two decimals. It can
be negative.

**Inputs:** `goal_difference` and `matches_played` from `mart__club_season`.

**available_from:** 1992-93.

**Limitations:** the current season is a small-sample rate. It compresses attack
and defence into one number, so a value near zero can hide a high-scoring, leaky
side just as easily as a cautious, tight one.
