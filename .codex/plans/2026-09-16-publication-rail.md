# Generated content through the PR rail

Owner: Codex; Laurea PR #10 and full gap-filling product/governance lane.

The scheduled workflow pushed assets directly to the default branch; the arena workflow rebased and pushed its leaderboard, then closed the source issue before any independent landing receipt. Replace both write paths with one scoped publisher. This implements the publication-rail follow-up in 2026-09-16-pr-validation.md.

The publisher accepts only the appropriate trusted workflow event, source SHA and workspace. It checks the Git remote against the repository identity, source ancestry on the default branch, an empty caller index and strictly scoped generated paths. It rejects symlinks and existing publication branches. Each run gets a unique branch; no force push, default-ref push, rebase, retry or merge command exists. Readback verifies the remote head and PR repository/head/base identity. A failed create preserves the published branch and reports its last verified state under the originating workflow run.

Arena publication additionally binds the issue to the event and current open issue. The PR closes that issue only when it lands; unchanged output creates no PR and leaves the source issue open. The existing issue response now says prepared, not published. Both workflows have ten-minute bounds and preserve running jobs through non-cancelling concurrency.

Validation uses isolated actual Git repositories and bare remotes, with the GitHub interface replaced by a fixture. No production publisher was invoked and no issue message was sent in this session. The tests cover default-ref preservation, scoped changes, caller files, existing branches, wrong destinations/heads, wrong source issues, ambiguous writes without retry, and redacted failure receipts. The full test and workflow-lint results are recorded in the PR before integration.

GitHub's current documented GITHUB_TOKEN behavior may hold created-PR workflows for approval. That platform authority remains intact; no alternative credential or automatic approval is introduced. Hosted admission, workflow execution, PR approval and landed publication remain separate acceptance obligations owned by this PR and its originating run.

Verification: PYTHONPATH=src python3 -m pytest -q passed all 105 tests. actionlint passed for laurea.yml, arena.yml and validate.yml. git diff --check passed. No production publishing, workflow approval, issue comment or issue closure was performed by this session.
