-- Every match from every source, resolved to canonical club ids, one row per
-- source per match. This is the reconciliation point and the input to the
-- cross-source agreement check. engsoccerdata names are canonical already and
-- resolve by a direct name join; football-data names resolve through its alias
-- file. A name that resolves to no id lands NULL, and the not_null test on the
-- club ids fails the build, which is the fail-closed behaviour of SPEC 4.5.
--
-- Competition-agnostic: no league name, no club count, no season length.

with eng as (
    select * from {{ ref('stg_engsoccerdata__matches') }}
),

fbd as (
    select * from {{ ref('stg_footballdata__matches') }}
),

clubs as (
    select * from {{ ref('stg_registry__clubs') }}
),

fbd_aliases as (
    select source_name, club_id
    from {{ ref('stg_registry__aliases') }}
    where source = 'football-data'
),

eng_resolved as (
    select
        'engsoccerdata'      as source,
        eng.competition_id,
        eng.season_start_year,
        eng.match_date,
        home.club_id         as home_club_id,
        away.club_id         as away_club_id,
        eng.home_goals,
        eng.away_goals
    from eng
    left join clubs as home on eng.home_club_name = home.club_name
    left join clubs as away on eng.away_club_name = away.club_name
),

fbd_resolved as (
    select
        'football-data'      as source,
        fbd.competition_id,
        fbd.season_start_year,
        fbd.match_date,
        home.club_id         as home_club_id,
        away.club_id         as away_club_id,
        fbd.home_goals,
        fbd.away_goals
    from fbd
    left join fbd_aliases as home on fbd.home_club_name = home.source_name
    left join fbd_aliases as away on fbd.away_club_name = away.source_name
)

select * from eng_resolved
union all
select * from fbd_resolved
