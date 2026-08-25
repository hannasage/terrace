-- Grain check: mart__club_season is one row per club per season. Any duplicate
-- (season_start_year, club_id) pair is returned and fails the build.

select
    season_start_year,
    club_id,
    count(*) as rows
from {{ ref('mart__club_season') }}
group by season_start_year, club_id
having count(*) > 1
