# METHODOLOGY — field definitions and publication boundary

## Scope

LAVREA is an API snapshot and renderer. It reports bounded GitHub activity
fields and deterministic descriptions of the repository corpus visible to one
run. It does not infer percentile rank, excellence, employability, authorship,
quality, reliability, adoption, or impact from activity volume.

The previous percentile model was withdrawn because GitHub does not publish the
per-user population distribution needed to verify those claims. Large values,
generic platform totals, national leaderboards, and informal medians do not
prove that a threshold is the 99th or 99.9th percentile of a defined population.

## Direct measurements

- `contributions_year` uses
  `contributionsCollection.contributionCalendar.totalContributions` and shows
  the API-provided commit, pull-request, review, issue, and restricted counts.
  A contribution event is not a standardized unit of shipped work.
- `pull_requests_year` uses
  `contributionsCollection.totalPullRequestContributions`. It counts opened
  pull requests; it does not report review, mergeability, or merge status.
- `repos_visible` counts `isFork=false` entries returned from the personal
  repositories connection and the repositories connections for organization
  memberships visible to the token. An organization repository is not thereby
  attributed to the measured account.
- `organization_memberships` reports the first 20 memberships returned by the
  current query. Membership is not operation or ownership.
- `tenure` derives elapsed time from `user.createdAt`; account age is not a
  substitute for continuous professional experience.

## Deterministic corpus descriptions

- `language_breadth` counts distinct `primaryLanguage.name` values. GitHub
  assigns one primary language per repository; the count does not prove
  individual proficiency or authorship.
- `language_layer_coverage` maps those labels through the table in
  `src/laurea/detectors.py`. It describes the visible corpus and is not a
  full-stack-engineer ranking.

## Token and provenance boundary

Visibility depends on the token. A user token can expose restricted contribution
counts and organization repositories unavailable to the default Actions token.
Every report records its subject, generation time, source repository, and source
SHA. Outside GitHub Actions, unavailable provenance is recorded as `unknown`
rather than fabricated.

The central scheduled workflow deliberately measures `4444J99`; template copies
and forks measure `github.repository_owner`. Reports with malformed repository
entries or incomplete contribution fields fail rather than silently publishing
partial aggregates.

## Reinstating a ranking

A future rank claim requires a versioned population dataset, a defined comparison
class and time window, reproducible quantile code, uncertainty handling, and a
review receipt tied to the exact dataset and implementation head. Until all of
those exist, LAVREA publishes no percentile.
