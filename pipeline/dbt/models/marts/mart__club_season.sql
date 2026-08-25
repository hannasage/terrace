-- Premier League club-season table. One row per club per season with the
-- standings quantities. This is a mart, so the competition-specific rule lives
-- here: three points for a win, one for a draw, which the Premier League has
-- used since its 1992 start.
--
-- Built by unioning each match twice, once from the home club's perspective and
-- once from the away club's, so every quantity is a straightforward aggregate.

with matches as (
    select * from {{ ref('core__match') }}
    where competition_id = 'eng_premier_league'
),

perspectives as (
    select
        season_start_year,
        home_club_id as club_id,
        home_goals   as goals_for,
        away_goals   as goals_against
    from matches
    union all
    select
        season_start_year,
        away_club_id as club_id,
        away_goals   as goals_for,
        home_goals   as goals_against
    from matches
)

select
    season_start_year,
    club_id,
    count(*)                                              as matches_played,
    sum(case when goals_for > goals_against then 1 else 0 end) as wins,
    sum(case when goals_for = goals_against then 1 else 0 end) as draws,
    sum(case when goals_for < goals_against then 1 else 0 end) as losses,
    sum(goals_for)                                       as goals_for,
    sum(goals_against)                                   as goals_against,
    sum(goals_for) - sum(goals_against)                  as goal_difference,
    3 * sum(case when goals_for > goals_against then 1 else 0 end)
        + sum(case when goals_for = goals_against then 1 else 0 end) as points
from perspectives
group by season_start_year, club_id
