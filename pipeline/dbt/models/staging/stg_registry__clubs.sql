-- Canonical clubs, read from the Parquet that scripts/registry_to_parquet.py
-- materialises from the hand-maintained clubs.<nation>.yml. The YAML is the
-- single source of truth; this model just exposes it to the transform so a
-- source club name can be resolved to a canonical id.

select
    club_id,
    club_name,
    nation
from read_parquet('pipeline/data/registry/clubs.parquet')
