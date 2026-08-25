-- Approved source-name to canonical-id mappings, read from the Parquet that
-- scripts/registry_to_parquet.py materialises from the hand-maintained
-- aliases.<source>.yml. One row per (source, source_name). The transform joins a
-- source's club names through here to resolve them to canonical ids.

select
    source,
    source_name,
    club_id
from read_parquet('pipeline/data/registry/aliases.parquet')
