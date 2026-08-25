-- Agreement: where both sources cover the same match, the scoreline must match.
-- A disagreement is returned and fails the build. Disagreements are listed, not
-- averaged (SPEC 4.6): a difference is a finding to investigate, usually a source
-- revising a result or a parser fault, never something to paper over.

with by_source as (
    select * from {{ ref('core__match_by_source') }}
),

eng as (
    select competition_id, season_start_year, home_club_id, away_club_id,
           home_goals, away_goals
    from by_source
    where source = 'engsoccerdata'
),

fbd as (
    select competition_id, season_start_year, home_club_id, away_club_id,
           home_goals, away_goals
    from by_source
    where source = 'football-data'
)

select
    eng.competition_id,
    eng.season_start_year,
    eng.home_club_id,
    eng.away_club_id,
    eng.home_goals  as eng_home_goals,
    eng.away_goals  as eng_away_goals,
    fbd.home_goals  as fbd_home_goals,
    fbd.away_goals  as fbd_away_goals
from eng
join fbd
  on eng.competition_id = fbd.competition_id
 and eng.season_start_year = fbd.season_start_year
 and eng.home_club_id = fbd.home_club_id
 and eng.away_club_id = fbd.away_club_id
where eng.home_goals is distinct from fbd.home_goals
   or eng.away_goals is distinct from fbd.away_goals
