# Arena stale table check

Owner: organvm/laurea PR #10 (draft).

`laurea arena-table --check` renders the complete accepted record set plus optional baseline in a temporary directory and compares exact bytes without rewriting the caller table. A newly accepted second entrant invalidates an earlier table; regeneration includes both entrants. Missing, oversized, and symlink table outputs fail closed.

PR validation invokes the check when LEADERBOARD.md changes, against the checked-out PR merge tree. Full checkout history provides the event base for changed-path detection; Git errors fail the step. Observation-only PRs remain independently mergeable and do not claim the existing table is fresh.

Validation: 18 arena tests passed in 0.18 seconds; workflow actionlint and git diff --check passed. Hosted execution and required-check enforcement remain unproven. This check detects stale table replacement on the tree it evaluates; it does not independently enforce GitHub branch protection or reject movement after a successful run.

Remaining concurrency integration: bounded post-record-merge publisher/continuation, exact source/default readback before preparing a table PR, and merge-time current-tree enforcement through the existing integration rail. PR #10 remains draft.
