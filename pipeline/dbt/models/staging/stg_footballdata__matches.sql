-- football-data.co.uk match results, Premier League only.
--
-- Source-shaped: renames and types, keeps the source club names for core to
-- reconcile through the alias registry. football-data's files carry real quirks
-- handled here and nowhere else:
--   * mixed latin-1 and utf-8 encoding across eras (read as latin-1, which never
--     fails on a byte),
--   * a byte-order mark on recent files that renames the first column, so the
--     division reads as div on clean files and idiv on marked ones; coalesced,
--   * columns that vary by era, handled by union_by_name and null_padding with
--     no ignore_errors, so nothing is silently dropped.
--
-- The division filter keeps only E0, the Premier League. The season comes from
-- the file name, which the adapter controls, not from the file contents. Because
-- ingest is change-gated per season, a season can appear under several snapshot
-- dates; the latest version of each season wins.

with raw as (
    select
        * exclude (filename),
        coalesce(div, idiv)                                as division,
        regexp_extract(filename, 'E0_(\d+)', 1)            as season_code,
        regexp_extract(filename, '(\d{4}-\d{2}-\d{2})', 1) as snapshot_date
    from read_csv(
        'pipeline/data/raw/football-data/*/E0_*.csv.gz',
        union_by_name = true,
        null_padding = true,
        filename = true,
        encoding = 'latin-1',
        normalize_names = true,
        types = {'fthg': 'VARCHAR', 'ftag': 'VARCHAR', 'date': 'VARCHAR'}
    )
    where hometeam is not null and hometeam <> ''
),

latest_per_season as (
    select *,
        max(snapshot_date) over (partition by season_code) as latest_date
    from raw
),

kept as (
    select * from latest_per_season
    where snapshot_date = latest_date
      and division = 'E0'
)

select
    'eng_premier_league'                           as competition_id,
    -- season_code 9394 -> 1993, 0001 -> 2000, 2526 -> 2025
    cast(
        case
            when cast(substr(season_code, 1, 2) as integer) >= 90
                then 1900 + cast(substr(season_code, 1, 2) as integer)
            else 2000 + cast(substr(season_code, 1, 2) as integer)
        end as integer
    )                                              as season_start_year,
    -- Dates are day/month/year, four-digit year on most files and two-digit on
    -- some early ones. The two-digit form is tried first, and the order matters:
    -- %Y happily reads '06/11/93' as the year 93 rather than failing, so putting
    -- it first silently dated 8524 matches to the first century. %y rejects a
    -- four-digit year outright, so it cannot claim a date that belongs to %Y.
    -- try_strptime returns NULL rather than erroring, and a NULL or an
    -- implausible date now fails the build through assert_match_date_sane,
    -- because mart__club_match orders a season by this column.
    cast(coalesce(
        try_strptime(date, '%d/%m/%y'),
        try_strptime(date, '%d/%m/%Y')
    ) as date)                                     as match_date,
    hometeam                                       as home_club_name,
    awayteam                                       as away_club_name,
    cast(fthg as integer)                          as home_goals,
    cast(ftag as integer)                          as away_goals
from kept
