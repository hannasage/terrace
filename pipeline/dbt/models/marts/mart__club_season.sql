-- Premier League club-season table. One row per club per season with the
-- standings quantities. This is a mart, so the competition-specific rule lives
-- here: three points for a win, one for a draw, which the Premier League has
-- used since its 1992 start.
--
-- Built by aggregating mart__club_match, the per-club-per-match grain. Metrics
-- that need individual matches (clean sheets, biggest win margin, win streaks)
-- come from the same source, so there is one canonical unnest.

with club_match as (
    select * from {{ ref('mart__club_match') }}
),

aggregated as (
    select
        season_start_year,
        club_id,
        count(*)                                              as matches_played,
        sum(case when result = 'W' then 1 else 0 end)         as wins,
        sum(case when result = 'D' then 1 else 0 end)         as draws,
        sum(case when result = 'L' then 1 else 0 end)         as losses,
        sum(goals_for)                                        as goals_for,
        sum(goals_against)                                    as goals_against,
        sum(goals_for) - sum(goals_against)                   as goal_difference,
        3 * sum(case when result = 'W' then 1 else 0 end)
            + sum(case when result = 'D' then 1 else 0 end)   as points,
        -- Match-derived metrics.
        sum(case when clean_sheet then 1 else 0 end)          as clean_sheets,
        max(case when result = 'W' then goal_margin end)      as biggest_win_margin
    from club_match
    group by season_start_year, club_id
),

-- Longest run of consecutive wins per club-season, gaps and islands: among a
-- club's wins in match order, match_number minus the wins' own row number is
-- constant inside one unbroken run, so grouping on it and counting gives each
-- run's length.
win_islands as (
    select
        club_id,
        season_start_year,
        match_number - row_number() over (
            partition by club_id, season_start_year order by match_number
        ) as run_group
    from club_match
    where result = 'W'
),

streaks as (
    select club_id, season_start_year, max(run_length) as longest_win_streak
    from (
        select club_id, season_start_year, run_group, count(*) as run_length
        from win_islands
        group by club_id, season_start_year, run_group
    )
    group by club_id, season_start_year
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
    cur.goal_difference - prev.goal_difference           as goal_difference_change_vs_prev,
    -- Match-derived metrics. A club that won no match has a null biggest margin
    -- (an honest gap) and a streak of zero.
    cur.clean_sheets,
    cur.biggest_win_margin,
    coalesce(streaks.longest_win_streak, 0)              as longest_win_streak
from with_bounds cur
left join aggregated prev
    on prev.club_id = cur.club_id
   and prev.season_start_year = cur.season_start_year - 1
left join streaks
    on streaks.club_id = cur.club_id
   and streaks.season_start_year = cur.season_start_year
