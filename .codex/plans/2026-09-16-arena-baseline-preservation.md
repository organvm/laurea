# Arena historical baseline preservation

Owner: organvm/laurea PR #10 (draft).

The historical leaderboard row is preserved in arena/baseline.json with source commit 90299a31cc77eccd0a5f2a33323f653683929e2b, original path, repository, SHA-256, and explicit date-only precision. arena/baseline-source.md is the exact git-show source bytes, retained so shallow CI can validate the migration. No issue number or precise observation timestamp was invented.

`laurea arena-table --entries DIRECTORY --baseline arena/baseline.json --leaderboard OUTPUT` validates the baseline, preserves it across unrelated entrants, rejects older replacements, and permits later observations to supersede it. Baseline use is explicit; no runtime workflow has yet changed.

Validation: combined arena/publication tests 34 passed in 7.96 seconds. After replacing test-time git-history access with the preserved source bytes, all 13 entry tests passed in 0.07 seconds. git diff --check exit 0. The source copy was obtained directly through git show of the named commit.

Remaining review 4023115101 acceptance: bounded post-merge table regeneration/publication, exact complete-source binding, stale generated table rejection, and continuation after independently merged issue records. Keep PR #10 draft until those integration tests pass.
