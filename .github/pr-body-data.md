Scheduled data refresh.

This pull request contains only new source snapshots and rebuilt artefacts. It
merges itself once every required check passes.

If it is still open, a check failed. The two usual causes need opposite
responses:

- **`assert_source_agreement`**: a source revised a scoreline. Read the diff,
  confirm it is a legitimate correction, approve.
- **Anything else, or agreement failing on many matches at once**: a parser
  likely broke. Do not approve. Assign the investigation.

Season completeness, club appearance counts, registry coverage and tier honesty
all run as part of the same gate. See `docs/PIPELINE.md` section 4.
