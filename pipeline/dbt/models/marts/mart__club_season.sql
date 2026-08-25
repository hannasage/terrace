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
),

aggregated as (
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
),

ranked as (
    select
        *,
        -- Rate metrics, which make seasons of different lengths comparable.
        round(points * 1.0 / matches_played, 2)          as points_per_game,
        round(wins * 1.0 / matches_played, 3)            as win_rate,
        round(goals_for * 1.0 / matches_played, 2)       as goals_for_per_game,
        round(goals_against * 1.0 / matches_played, 2)   as goals_against_per_game,
        round(goal_difference * 1.0 / matches_played, 2) as goal_difference_per_game,
        -- Share of the maximum points available (three per match).
        round(points * 1.0 / (3 * matches_played), 3)    as points_share,
        -- Final league position. The Premier League breaks ties on points, then
        -- goal difference, then goals scored; head-to-head, used only in rare
        -- historical cases, is not modelled. 1 is champions.
        rank() over (
            partition by season_start_year
            order by points desc, goal_difference desc, goals_for desc
        )                                                as league_position,
        count(*) over (partition by season_start_year)   as clubs_in_season
    from aggregated
),

with_bounds as (
    select *, max(season_start_year) over () as current_season
    from ranked
)

select
    cur.season_start_year,
    cur.club_id,
    cur.matches_played,
    cur.wins,
    cur.draws,
    cur.losses,
    cur.goals_for,
    cur.goals_against,
    cur.goal_difference,
    cur.points,
    cur.points_per_game,
    cur.win_rate,
    cur.goals_for_per_game,
    cur.goals_against_per_game,
    cur.goal_difference_per_game,
    cur.points_share,
    cur.league_position,
    -- Standing flags are undetermined while the season is in progress, so they
    -- are null for the current season rather than a premature true or false.
    case
        when cur.season_start_year = cur.current_season then null
        when cur.league_position = 1 then 1 else 0
    end                                                  as is_champion,
    -- Relegation is the bottom three, except the bottom four at the end of
    -- 1994/95 when the Premier League cut from 22 clubs to 20.
    case
        when cur.season_start_year = cur.current_season then null
        when cur.league_position >
             cur.clubs_in_season - (case when cur.season_start_year = 1994 then 4 else 3 end)
            then 1 else 0
    end                                                  as relegated,
    -- Change versus the club's immediately previous season, when that was the
    -- calendar year before. Null when the club was absent from the league then.
    cur.points - prev.points                             as points_change_vs_prev,
    cur.goal_difference - prev.goal_difference           as goal_difference_change_vs_prev
from with_bounds cur
left join aggregated prev
    on prev.club_id = cur.club_id
   and prev.season_start_year = cur.season_start_year - 1
