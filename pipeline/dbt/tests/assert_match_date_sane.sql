-- Every Premier League match must have a date that could belong to its season.
--
-- This replaces an earlier assertion that only checked for NULL. That was too
-- weak: football-data writes some early dates with a two-digit year, and
-- try_strptime with '%d/%m/%Y' reads '06/11/93' as the year 93 rather than
-- failing. 8524 matches across 1993/94 to 2016/17 were dated to the first
-- century and passed a not-null check without complaint.
--
-- mart__club_match numbers a club's season by this column, so a wrong date
-- reorders a season and can miscount longest_win_streak. A date is a finding
-- when it is missing and equally when it is impossible.
--
-- The window is deliberately loose. A season starting in year Y runs from
-- August Y to May Y+1, stretched to July in 2019/20 by the pandemic, so
-- anything from June Y to September Y+1 is accepted and anything outside it is
-- a parser fault worth stopping the build for.

select
    match_id,
    season_start_year,
    match_date,
    home_club_id,
    away_club_id
from {{ ref('core__match') }}
where competition_id = 'eng_premier_league'
  and (
      match_date is null
      or match_date < make_date(season_start_year, 6, 1)
      or match_date > make_date(season_start_year + 1, 9, 30)
  )
