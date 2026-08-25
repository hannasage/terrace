-- Conformed matches, one row per match, deduplicated across sources.
--
-- Two sources cover overlapping matches. Per D-004, football-data is primary
-- from 1993/94 and engsoccerdata is the spine and sole source for 1992/93 (and
-- the cross-check everywhere else). So for each match, football-data wins when it
-- has the match, and engsoccerdata fills the rest. The scores of the two sources
-- are checked for agreement separately by assert_source_agreement; here we just
-- pick the primary row.
--
-- The match key is competition, season, and the two club ids, not the date: the
-- same fixture is one match even if the sources disagree on the exact day. Each
-- ordered club pair meets once per season, so the key is unique.

with by_source as (
    select * from {{ ref('core__match_by_source') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by competition_id, season_start_year, home_club_id, away_club_id
            order by case source when 'football-data' then 0 else 1 end
        ) as source_rank
    from by_source
)

select
    md5(concat_ws(
        '|',
        competition_id,
        cast(season_start_year as varchar),
        home_club_id,
        away_club_id
    ))                       as match_id,
    competition_id,
    season_start_year,
    match_date,
    home_club_id,
    away_club_id,
    home_goals,
    away_goals,
    source
from ranked
where source_rank = 1
