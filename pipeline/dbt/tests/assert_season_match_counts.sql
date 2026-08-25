-- Completeness: every Premier League season present must have the expected
-- number of matches. 462 for the 22-club seasons 1992/93 to 1994/95, 380 for
-- the 20-club seasons from 1995/96. A season whose count is anything else is
-- returned and fails the build.
--
-- This checks the count of each season that exists. It does not yet assert that
-- every season in the range is present: engsoccerdata is missing 2022/23 (a
-- known gap, D-004), and that season is filled by football-data once its alias
-- lands. The all-seasons-present check arrives with that second source.

with per_season as (
    select
        season_start_year,
        count(*) as match_count
    from {{ ref('core__match') }}
    where competition_id = 'eng_premier_league'
    group by season_start_year
),

expected as (
    select
        season_start_year,
        match_count,
        case
            when season_start_year between 1992 and 1994 then 462
            when season_start_year >= 1995 then 380
        end as expected_count
    from per_season
)

select *
from expected
where match_count <> expected_count
