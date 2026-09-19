# Arena race verification and issue acceptance correction

Owner: organvm/laurea PR #10 (draft).

Current source before this batch: 39b4c00. Real-Git refresh tests now inject timeout before write, timeout after successful write, and a competing fast-forward update. Each permits at most one attempted publisher push; the successful ambiguous write is reconciled by readback, absent writes remain unverified, and the concurrent update is preserved. Prepared-head and predecessor ownership survive failure receipts. Publication suite: 30 passed in 17.97 seconds.

Live review 4023513093 correctly identified premature record-stage issue closure. The automatic Closes keyword is removed from observation PRs, and workflow response text explicitly keeps the issue open until accepted table materialization. Focused corrected-contract test: 1 passed in 0.92 seconds. Workflow lint passed. Automatic issue settlement after table acceptance still needs a separately verified implementation; source-record acceptance is no longer mislabeled as that outcome.

Live review 4023513106 identifies the same pending-proposal proliferation risk in the daily metrics publisher. The current table-only ownership guard does not cover metrics. Next action: extend bounded same-repository predecessor discovery and safe reconciliation to the metrics artifact scope, preserving the normal-push and exact-head readback invariants.

Review 4023185214 remains backed by the separate immutable-identity supplement; the historical observation is preserved. PR #10 stays draft pending final source review, issue settlement, metrics reconciliation, and hosted enforcement evidence.
