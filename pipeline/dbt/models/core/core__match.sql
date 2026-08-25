-- Conformed matches, competition-agnostic. One row per match, with both clubs
-- resolved to canonical ids. This is the reconciliation point: a source club
-- name that does not resolve to a canonical id lands as NULL, and the not_null
-- test on home_club_id / away_club_id fails the build, which is the fail-closed
-- behaviour of SPEC 4.5 and D-009. engsoccerdata names already match the
-- registry, so nothing is NULL here today; football-data joins in later through
-- its alias file.
--
-- Nothing in this model names the Premier League or assumes a club count or a
-- season length. The competition is carried as an id from staging.

with matches as (
    select * from {{ ref('stg_engsoccerdata__matches') }}
),

clubs as (
    select * from {{ ref('stg_registry__clubs') }}
)

select
    md5(concat_ws(
        '|',
        matches.competition_id,
        cast(matches.season_start_year as varchar),
        cast(matches.match_date as varchar),
        home.club_id,
        away.club_id
    ))                                 as match_id,
    matches.competition_id,
    matches.season_start_year,
    matches.match_date,
    home.club_id                       as home_club_id,
    away.club_id                       as away_club_id,
    matches.home_goals,
    matches.away_goals
from matches
left join clubs as home on matches.home_club_name = home.club_name
left join clubs as away on matches.away_club_name = away.club_name
