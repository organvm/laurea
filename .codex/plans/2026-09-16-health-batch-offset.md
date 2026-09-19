# Continue bounded health inspection without restarting the inventory

Owner: Laurea PR #10, Codex gap-filling-20260915.

Live six-target batch at source f101d3c preserves all six inventory entries: one public identity observed, five attempts unmeasured under the shared budget. Receipt: docs/receipts/six-target-health-batch-20260916.json. This is diagnostic observation, not relay execution or acceptance.

Add an explicit offset to inspect a later contiguous slice without rereading earlier entries or redefining the inventory denominator. Record selection bounds and retain unattempted entries; invalid offsets fail before network reads. Separate batches retain independent observation times and cannot imply simultaneous estate health.

Verification: all 123 tests pass in 6.25 seconds; diff hygiene passes. Exact-head hosted validation for previous source f101d3c failed at run 35062917083, job 104686859726, with zero steps. It provides no executed test result; admission cause and remedy remain unverified.
