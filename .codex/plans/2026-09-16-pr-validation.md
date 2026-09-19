# Read-only pull-request validation

Owner: Codex; Laurea PR #10, gap-filling product verification.

Live workflow inventory lists laurea.yml, arena.yml, and dynamic dependency/code-scanning workflows. Repository tests were reachable only from the publishing workflow's default-branch events; the PR did not have its own repository-test job.

Add validate.yml for pull requests and main pushes. The job runs the existing test command on Python 3.12 with a ten-minute deadline, read-only contents permission, no repository secrets, and checkout credential persistence disabled. Concurrency preserves running work. Both action SHAs were resolved from their owning repositories' current v7/v6 tags before implementation.

The current source passed 92 tests in the preceding implementation batch. This workflow-only change requires actionlint and diff hygiene; a hosted zero-step result remains unexecuted verification. No workflow dispatch, account grant, paid capacity expansion, or branch-policy change is part of this patch.

The existing publication workflows still require conversion from direct default-branch writes to the declared PR rail. That engineering work remains owned by this PR and the full gap-filling product lane; the read-only test job is not publication acceptance. Hosted admission remains its separate existing owner.

Validation: actionlint .github/workflows/validate.yml and git diff --check both passed. The source tests are unchanged from the preceding 92-test batch; no green test suite was replayed for this YAML-only addition.
