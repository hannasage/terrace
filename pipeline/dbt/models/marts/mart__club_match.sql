-- Premier League matches at club grain: one row per club per match, the layer
-- between core__match (one row per match) and mart__club_season (one row per club
-- per season). Each match becomes two rows, once from each club's side, which is
-- the same unnest mart__club_season used inline but enriched with the match id,
-- the date, the opponent, and per-match result facts. Club-season metrics that
-- depend on individual matches (clean sheets, biggest win margin, win streaks)
-- aggregate up from here.
--
-- match_number gives a deterministic order within a club's season, so a run of
-- consecutive results can be counted. The order is by date, then match id as a
-- stable tie-break for the rare two-matches-a-day case. assert_match_date_present
-- guarantees the date is never null, so the order is total.

with matches as (
    select * from {{ ref('core__match') }}
    where competition_id = 'eng_premier_league'
),

perspectives as (
    select
        competition_id,
        season_start_year,
        match_id,
        match_date,
        home_club_id as club_id,
        away_club_id as opponent_club_id,
        true         as was_home,
        home_goals   as goals_for,
        away_goals   as goals_against
    from matches
    union all
    select
        competition_id,
        season_start_year,
        match_id,
        match_date,
        away_club_id as club_id,
        home_club_id as opponent_club_id,
        false        as was_home,
        away_goals   as goals_for,
        home_goals   as goals_against
    from matches
)

select
    competition_id,
    season_start_year,
    match_id,
    match_date,
    club_id,
    opponent_club_id,
    was_home,
    goals_for,
    goals_against,
    goals_for - goals_against                    as goal_margin,
    case
        when goals_for > goals_against then 'W'
        when goals_for = goals_against then 'D'
        else 'L'
    end                                          as result,
    goals_against = 0                            as clean_sheet,
    row_number() over (
        partition by club_id, season_start_year
        order by match_date, match_id
    )                                            as match_number
from perspectives
