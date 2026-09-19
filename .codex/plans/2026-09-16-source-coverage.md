# Explicit source coverage

Owner: Codex. Implements the Laurea coverage tranche of Limen's gap-filling plan.

The collector previously omitted failed organizations and stopped membership
scope at 20. Paginate both connections with finite limits, stable totals and
advancing cursors. Preserve failed sources as unmeasured. Record immutable public
repository IDs and current default SHAs; exclude private repository identities
while retaining counts. Collection completeness is distinct from health evidence.

Verification, security and PR readiness remain explicitly unmeasured. Follow-up
must collect exact-generation executed checks, security obligations and current
PR acceptance; token-visible memberships cannot replace the 326-repository
administered estate denominator. No deployment or estate-health acceptance is
claimed by this source-coverage implementation.

Verification: `PYTHONPATH=src python3 -m pytest -q`.
Pagination reference: https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api

## Executed health observation tranche

A bounded read-only `health --repo OWNER/NAME` command now binds repository ID
and default SHA before and after collection. It distinguishes executed steps
from run conclusions and preserves inaccessible/truncated evidence. Alert
counts exclude details; private repositories are excluded before deeper reads.

Live read at 2026-09-16T02:06:52Z: organvm/laurea repository ID 1289397231,
default faf6c5f67130925518233f5f99a76182b544fb85 remained current. Ten of 21
runs were inspected, all with zero executed steps; 11 remain unmeasured.
Dependabot and code-scanning returned zero open alerts; secret-scanning was
unmeasured. One open PR was observed; readiness remains unmeasured. This is
not executed code verification or estate acceptance. Representative run:
https://github.com/organvm/laurea/actions/runs/34980815908

Follow-up: bind registered verification obligations and security coverage,
collect exact-head PR acceptance, and reconcile administered-estate authority.
API references: https://docs.github.com/en/rest/actions/workflow-runs and
https://docs.github.com/en/rest/actions/workflow-jobs
