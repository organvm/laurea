# Arena pending proposal ownership

Owner: organvm/laurea PR #10 (draft).

The table publisher now reads a bounded inventory of open PRs before staging or creating a branch. Existing same-repository automation/arena-table branches are bound to exact head, repository, default base, and PR number; each is returned in a pending_predecessor receipt. No replacement branch, index mutation, or duplicate PR occurs. Saturated or malformed inventories fail closed. Multiple existing proposals remain explicitly owned rather than being automatically discarded.

Verification: full suite 149 passed in 10.70 seconds. Subsequently added end-to-end isolated Git test passed in 1.59 seconds: two branches originating at one base each commit one entrant, merge independently, and feed a generated table PR containing both entrants plus the historical baseline. The remote default remains at the accepted-record commit and the generated PR changes only LEADERBOARD.md. git diff --check passed.

Pending ownership is not automatic refresh or completed concurrency acceptance. A stale predecessor still requires safe reconciliation through its existing PR before continuation can publish the current table. Source-default checks do not establish merge-time branch protection. PR #10 remains draft pending those integration obligations and hosted execution.
