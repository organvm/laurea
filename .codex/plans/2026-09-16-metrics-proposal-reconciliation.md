# Metrics proposal reconciliation

Owner: organvm/laurea PR #10; review 4023513106.

The daily metrics workflow now opts into bounded pending-proposal refresh and fetches ancestry. Publisher ownership discovery covers both metrics and arena-table branches, retaining multiple proposals as explicit pending owners. Metrics requires the current default generation. A single assets-only predecessor can advance through a normal fast-forward push with both predecessor/default parents; unrelated changes and generated symlinks fail closed. Existing ambiguity handling remains one write attempt and one readback.

The isolated-Git metrics integration test proves the existing branch gains current metrics and newer default files, preserves both parent commits, leaves default unchanged, and creates no duplicate PR or force push. It passed in 1.43 seconds. The preceding publication suite passed 30 tests in 18.04 seconds, and workflow lint/diff checks passed. Full final-source suite: 156 passed in 19.24 seconds.

These are source and local Git receipts. Hosted admission, server-side enforcement, generated-PR checks, merge, and deployed behavior are not established. Arena issue settlement remains separately incomplete. Keep PR #10 draft pending final acceptance review.
