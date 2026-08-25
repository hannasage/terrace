-- engsoccerdata match results, Premier League only.
--
-- Source-shaped: renames and types the raw columns, filters to the top tier from
-- 1992/93 (the Premier League era), and nothing else. No joins, no reconciliation
-- here; that is core's job. engsoccerdata is a single monolithic file re-captured
-- whole on each change, so the latest snapshot is simply the newest dated file.
--
-- The competition is tagged here because staging knows what it is reading: tier 1
-- from 1992 is the Premier League. core stays competition-agnostic.

with raw as (
    select
        *,
        regexp_extract(filename, '(\d{4}-\d{2}-\d{2})', 1) as _snapshot_date
    from read_csv_auto(
        'pipeline/data/raw/engsoccerdata/*/england.csv*',
        filename = true
    )
),

latest as (
    select * from raw
    where _snapshot_date = (select max(_snapshot_date) from raw)
)

select
    'eng_premier_league'          as competition_id,
    cast(Season as integer)       as season_start_year,
    cast(Date as date)            as match_date,
    home                          as home_club_name,
    visitor                       as away_club_name,
    cast(hgoal as integer)        as home_goals,
    cast(vgoal as integer)        as away_goals
from latest
where tier = '1'
  and cast(Season as integer) >= 1992
