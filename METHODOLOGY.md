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
  `contributionsCollection.contributionCalendar.totalContributions`. It also
  shows associated API fields for commits, pull requests, reviews, and issues;
  those fields are neither disjoint nor an additive breakdown of the calendar
  total. A contribution event is not a standardized unit of shipped work.
- `pull_requests_year` uses
  `contributionsCollection.totalPullRequestContributions`. It counts opened
  pull requests; it does not report review, mergeability, or merge status.
- `repos_visible` counts `isFork=false` entries returned from the personal
  repositories connection and the repositories connections for organization
  memberships visible to the token. An organization repository is not thereby
  attributed to the measured account.
- `organization_memberships` paginates the memberships visible to the token. Membership is not operation or ownership.
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

The central scheduled workflow deliberately measures `4444J99`. Personal copies
default to `github.repository_owner`; an organization-owned copy must set the
repository variable `LAUREA_LOGIN` to the user account it is authorized to
measure. Non-user subjects, malformed repository entries, and incomplete
contribution fields fail clearly rather than silently publishing partial
aggregates.

## Reinstating a ranking

A future rank claim requires a versioned population dataset, a defined comparison
class and time window, reproducible quantile code, uncertainty handling, and a
review receipt tied to the exact dataset and implementation head. Until all of
those exist, LAVREA publishes no percentile.

## Coverage and private corpus aggregates

Membership discovery counts as one attempted source alongside each repository
connection. Incomplete or malformed coverage stops report, arena, and verdict
publication before replacing existing assets or same-day history. The collector
can still return an explicitly unmeasured diagnostic snapshot.

Private repository identities are excluded from published rows. Identity-free
non-fork counts, primary-language counts, and stars retain the token-visible
corpus definition used by the existing metrics, hero, arena, and verdict series.
Forks remain excluded from language/non-fork metrics and included in estate star
totals, matching the previous definitions. Redaction without these aggregate
receipts cannot be published as the same metric. Legacy unredacted v2 snapshots
retain their recorded field semantics; they gain no new coverage claim.

The bounded health reader observes PR head/base generations, check counts and
current-head review decisions for up to five open PRs. It re-reads each PR before
marking its generation current. Draft and conflict blockers are separate from
required policy, trusted producer, execution, and acceptance evidence. Check
success or an approval count cannot establish readiness by itself. GitHub's
[review API](https://docs.github.com/en/rest/pulls/reviews#list-reviews-for-a-pull-request)
returns reviews in chronological order; comment-only reviews do not replace a
reviewer's decision.

Security observations use the documented
[Dependabot vulnerability severity](https://docs.github.com/en/rest/dependabot/alerts#list-dependabot-alerts-for-a-repository)
and [code-scanning security severity](https://docs.github.com/en/rest/code-scanning/code-scanning#list-code-scanning-alerts-for-a-repository)
fields. A code-quality `error` or `warning` does not supply security severity.
Missing or malformed severities stay in an explicit unmeasured bucket. A full
100-alert page retains observed counts but cannot establish complete coverage.
[Secret-scanning alerts](https://docs.github.com/en/rest/secret-scanning/secret-scanning#list-secret-scanning-alerts-for-a-repository)
contribute credential-obligation counts only; their contents and locations are
never serialized. Scanner enablement, recent scan coverage, and required policy
remain unmeasured even when an alert endpoint returns an empty list.

The health command's repository denominator is exactly one requested repository.
Known private repositories count as excluded without revealing their identity;
unknown visibility remains unmeasured. Archived public repositories count as
included and carry their archive status. This scope does not imply coverage of
the administered estate or establish a health percentage.
