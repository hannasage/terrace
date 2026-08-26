-- Grain check: mart__club_match is one row per club per match. Any duplicate
-- (season_start_year, club_id, match_id) triple is returned and fails the build.

select
    season_start_year,
    club_id,
    match_id,
    count(*) as rows
from {{ ref('mart__club_match') }}
group by season_start_year, club_id, match_id
having count(*) > 1
