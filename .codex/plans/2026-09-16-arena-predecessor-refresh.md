# Arena predecessor refresh

Owner: organvm/laurea PR #10 (draft).

The workflow opts into `--refresh-table`. Exactly one verified pending table proposal may advance; multiple proposals retain explicit owners for reconciliation. The refresh reads the exact remote head, fetches it, and verifies its changes since the shared ancestor affect only LEADERBOARD.md. It builds a new commit from the validated current-default tree plus generated table, with both predecessor and current default as parents. A normal push advances the existing branch without force, rebase, duplicate PR, default write, or loss of accepted records. A concurrent branch update causes normal non-fast-forward rejection and one bounded readback; no retry occurs. An equal tree reuses the predecessor.

The workflow fetches history for ancestry validation. Failure receipts retain the predecessor PR/branch and any prepared commit before attempting push. The result claims a verified branch refresh only; PR merge, hosted checks, server-side enforcement, and default adoption are separate.

Validation: full suite 152 passed in 14.43 seconds after fixing a test double for the new argument. Workflow lint and diff check passed. Real isolated-Git tests verify both-parent ancestry, unchanged remote default, newly accepted entrant retention, no new PR or force push, and rejection of unrelated predecessor changes. A subsequent publication-only run verifies the receipt-field refinement.

Remaining acceptance: exercise ambiguous refresh/concurrent movement explicitly, verify the current full source against review findings, and establish actual merge-time enforcement/hosted execution. PR #10 remains draft until source acceptance is complete.
