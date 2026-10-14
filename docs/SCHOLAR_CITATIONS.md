# Google Scholar citations

## Current state

Audited October 13, 2026 (America/Mexico_City), against main commit
`eee5a26179a1fa5387d908b05158d2dc9fe35dd6`.

No Google Scholar profile for Renatto Tommasi Hernández could be verified through
public name searches, site configuration, or the linked ORCID record. This does
not establish that no profile exists. No guessed ID has been added.

The workflow API reported `Update Google Scholar Citations` as **active** (ID
299048483). Its latest run, [38500236876](https://github.com/renatto-tommasi/renatto-tommasi.github.io/actions/runs/38500236876),
was labelled successful, but its logs show `ModuleNotFoundError` for
`bibtexparser.bibdatabase`. The workflow swallowed the updater's exit code.
Even after fixing dependencies, the missing `scholar_userid` blocks updates.

The live `/publications/` HTML contained the two personal bibliography entries,
no Einstein text, and no Scholar citation badge/link. Neither entry configured a
`google_scholar_id`. The unrelated June 17 cache was therefore not observed on
the publication page, but has been replaced with an empty cache to prevent future
accidental display. Scholar badges are explicitly off. Scheduled fetching is
paused; manual dispatch remains available and fails clearly if unconfigured.

## Publication record

Crossref's ACM deposit exactly matches the IntRob paper title and identifies
Renatto with ORCID `0009-0003-4960-4542`:

- DOI: [10.1145/3831600.3831606](https://doi.org/10.1145/3831600.3831606)
- Proceedings of the Intelligent Robotics FAIR 2026, ACM, pages 40–47.
- Authors in deposited order: Renatto Tommasi Hernández, Zoltán Istenes,
  Goran Vasiliević.
- [Crossref metadata](https://api.crossref.org/works/10.1145/3831600.3831606)
- [Conference program](https://introbfair26.inf.elte.hu/venueandprogram)

The bibliography now follows that published record. The IAC entry was not
changed because its DOI has not been verified.

## Enable after profile verification

1. Obtain the public Scholar profile URL. Match the name, affiliations and paper
   collection against the published record above. Use the exact `user` query
   parameter as `scholar_userid` in `_data/socials.yml`.
2. Install `bin/requirements-scholar.txt`. It pins scholarly and the compatible
   bibtexparser v1 API; the root requirements file includes it too.
3. Run `python -m unittest discover -s test -p 'test_scholar_citations.py'`, then
   `timeout 90 python bin/update_scholar_citations.py`. A missing ID, network error,
   mismatched author/publication ID or incomplete response must fail without
   overwriting the last successful snapshot. Review the fetched titles and
   counts before committing anything.
4. For each verified matching paper, set its BibTeX `google_scholar_id` to the
   publication suffix after `user_id:`. Turn
   `enable_publication_badges.google_scholar` back on and build the site. Confirm
   rendered badges point to the correct author and publication.
5. Restore `schedule` with `cron: "0 0 * * 1,3,5"` alongside `workflow_dispatch`.
   If GitHub marks the workflow `disabled_inactivity`, enable it in Actions.
   Dispatch manually and inspect both logs and conclusion. Do not claim a
   successful refresh from a green job alone.
6. Ensure refreshed data reaches the published site. Commits pushed using
   `GITHUB_TOKEN` normally do not trigger the push-based deployment workflow.
   Either dispatch `Deploy site` explicitly after a successful changed snapshot,
   add a carefully scoped workflow-run deployment trigger, or use the
   repository's documented scoped PAT setup. Do not add a token without review.

The updater performs bounded retries, validates author/publication ID ownership,
and replaces the cache atomically only after processing the complete response.
The workflow propagates failures, grants explicit write permission, serializes
updates and commits only the cache. Scholar scraping can still be rate-limited;
no live fetch is claimed until a verified profile actually succeeds.

## Validation for this repair

Offline tests cover absent configuration, first fetch without a cache, repeat
refreshes, network failure, wrong-profile/partial data, and failed atomic writes.
YAML parsing, bibliography metadata checks, changed-file Prettier checks and the
starter style contract are also run. A full Jekyll build requires Ruby/Bundler;
if unavailable locally, use the repository's Deploy site PR build before merging.
