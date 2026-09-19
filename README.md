# LAVREA — measured GitHub activity with provenance

LAVREA snapshots the GitHub fields visible to a run, derives a small set of
bounded corpus descriptions, and renders the result as SVG cards. It publishes
counts and definitions, not percentile rank or engineering-quality claims.

<p align="center">
  <img src="assets/cards/hero.svg" alt="Measured GitHub activity profile" width="800"/>
</p>

<p align="center">
  <img src="assets/cards/contributions_year.svg" alt="Contribution activity" width="420"/>
  <img src="assets/cards/repos_visible.svg" alt="Visible non-fork repository corpus" width="420"/>
</p>
<p align="center">
  <img src="assets/cards/language_breadth.svg" alt="Primary-language breadth" width="420"/>
  <img src="assets/cards/language_layer_coverage.svg" alt="Mapped language-layer coverage" width="420"/>
</p>

The generated report is [PROFILE.md](assets/PROFILE.md). The field definitions
and publication boundary are in [METHODOLOGY.md](METHODOLOGY.md).

## What the snapshot contains

- GitHub contribution-calendar events and associated API-provided fields;
- pull requests opened in the trailing contribution collection;
- non-fork repositories visible across the personal account and returned
  organization memberships;
- GitHub-assigned primary-language labels across that visible corpus;
- the account creation date and organization memberships visible to the token.

These observations do not establish individual authorship for organization
repositories, pull-request review or merge state, code quality, reliability,
adoption, business impact, or engineering rank.

## The arena

An issue titled `arena: your-login` asks CI to compute the same bounded fields
for another public account and update [LEADERBOARD.md](LEADERBOARD.md). The table
orders rows by activity count for navigation; it is not a quality ranking.

## Run it on yourself

1. Use the repository as a template or fork it.
2. Enable Actions. The canonical `organvm/laurea` repository tracks `4444J99`;
   a personal copy defaults to its repository owner. An organization-owned copy
   must set the repository variable `LAUREA_LOGIN` to the user account it is
   explicitly authorized to measure.
3. Optionally add a `LAUREA_TOKEN` secret if the run should include restricted
   contribution counts and private organization visibility.
4. Embed a generated card, for example
   `https://raw.githubusercontent.com/YOU/laurea/main/assets/cards/hero.svg`.

```bash
pip install -e '.[test]'
laurea run --login YOUR_LOGIN
laurea axes
python -m pytest tests -q
```

LAVREA has zero runtime dependencies. Add an observation with one registered
function in `src/laurea/detectors.py`; every observation must name its source
field or deterministic transformation and state its interpretive boundary.

## License

MIT.

## Bounded repository health observations

`laurea health --repo OWNER/NAME` reads one public repository with a 60-second,
40-request budget. It binds observations to the immutable repository ID and
checks the default SHA again after collection. The command publishes alert
counts only and excludes private repository identities.

Run conclusions and executed steps are separate fields. Zero-step failures do
not establish executed code failures. Truncated or inaccessible sources remain
unmeasured. Current generation, an empty alert list, or an open PR count does
not establish the owning acceptance predicate, enabled security coverage or PR
readiness. Until those obligations have their own evidence, health is unmeasured
and the command returns 77. This command does not dispatch workflows or merge PRs.

PR observations inspect at most five open PRs within the same request budget.
Each row binds its head and base before and after checks/reviews; omitted PRs
remain counted. Known draft/conflict blockers are reported separately from
unmeasured acceptance and required policy. Public reports preserve aggregate
metrics for token-visible private repositories without publishing their names.
Incomplete collection stops publication before replacing valid assets/history.

Health scope accounts for the one requested repository as public-observed,
private-excluded, or unmeasured; archived public repositories remain included.
Security summaries include observed critical/high/medium/low vulnerability counts,
unknown severities, and separate credential-alert counts. These are repository-wide
alert observations, not scans bound to the current default SHA. No alert contents,
locations, secret values, or account metadata are published.

## Bounded inventory health

For bounded health inspection across a declared inventory, use
`laurea health-batch --inventory inventory.json --limit 5`. The input is a JSON
array of unique `OWNER/NAME` strings. One batch shares the existing 40-request,
60-second read budget; the limit accepts 1–20 entries. The output retains the full
input denominator, unattempted entries, private exclusions, and unknown results.
Use `--offset N` to inspect a later slice without repeating earlier reads; the
reported selection offsets refer to the same supplied inventory. Separate batches
retain their own observations and do not establish one simultaneous healthy estate.
It does not establish that the supplied inventory is complete or that repositories
are healthy. Exit 77 preserves that unmeasured acceptance state. Private and
uninspected repository names are omitted from the output.

## Generated-content publication

The scheduled metrics and issue-driven arena workflows prepare generated-content
PRs on unique branches. They do not push to the default branch or merge their PRs.
The publisher verifies its source commit, destination repository, allowed changed
paths, remote branch tip, and resulting PR identity. A failed or ambiguous write
is reconciled by a readback, never a blind retry. Failed PR creation leaves the
remote branch and owning workflow receipt available for recovery.

Arena observation PRs preserve one record per issue. After records land, the table
workflow renders all accepted records plus the historical baseline and prepares a
table PR. A single existing table or metrics proposal can be refreshed with a
normal fast-forward push; multiple predecessors remain explicitly owned for
reconciliation. Unrelated predecessor changes are rejected. PR validation checks
that proposed tables match their complete input set.

Observation acceptance does not close the source issue. Issue closure remains
human-owned after the table is accepted on the default branch. Inspect local row
evidence without modifying files or issues:

```sh
laurea arena-table --entries arena/entries --baseline arena/baseline.json --settlement-report
```

This report identifies represented and superseded observations and hashes the
inspected inputs. It is local evidence: it does not establish that the inspected
commit is the current remote default, that a PR merged, or that an issue closed.
An unchanged snapshot does not create a PR or close an issue. GitHub documents that the
`opened`, `synchronize`, and `reopened` events for PRs created or updated with
`GITHUB_TOKEN` create approval-required workflow runs. A repository writer can
start those runs using **Approve workflows to run** in the PR merge box; see the official
[workflow-trigger contract](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
Opening a PR, receiving workflow approval, passing checks, and merging remain
distinct events. Repository/account admission and publication permission failures
remain visible; the publisher does not change those settings or substitute tokens.
