-- Every Premier League match must have a date. football-data derives match_date
-- with try_strptime, which yields NULL on a date string it cannot parse, so a
-- null can slip through unnoticed. The longest_win_streak metric orders a club's
-- matches by date, and a null date would sort unpredictably and miscount a run,
-- so a missing date is a finding that fails the build rather than a silently wrong
-- streak. Any offending match is returned.

select
    match_id,
    season_start_year,
    home_club_id,
    away_club_id
from {{ ref('core__match') }}
where competition_id = 'eng_premier_league'
  and match_date is null
