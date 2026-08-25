-- Completeness: every completed Premier League season must have the expected
-- number of matches. 462 for the 22-club seasons 1992/93 to 1994/95, 380 for the
-- 20-club seasons from 1995/96. A completed season with any other count is
-- returned and fails the build.
--
-- The current season is in progress and legitimately has fewer matches, so it is
-- exempt from the exact count and only required to be non-empty. The current
-- season is identified deterministically as the maximum season present, never by
-- reading the clock, so this holds every year without a code change.

with per_season as (
    select
        season_start_year,
        count(*) as match_count
    from {{ ref('core__match') }}
    where competition_id = 'eng_premier_league'
    group by season_start_year
),

bounds as (
    select max(season_start_year) as current_season from per_season
),

checked as (
    select
        per_season.season_start_year,
        per_season.match_count,
        bounds.current_season,
        case
            when per_season.season_start_year between 1992 and 1994 then 462
            when per_season.season_start_year >= 1995 then 380
        end as expected_count
    from per_season
    cross join bounds
)

select *
from checked
where
    -- completed seasons must hit the exact count
    (season_start_year < current_season and match_count <> expected_count)
    -- the current season just has to have started
    or (season_start_year = current_season and match_count = 0)
