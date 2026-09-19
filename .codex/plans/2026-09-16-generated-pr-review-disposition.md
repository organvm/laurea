# Generated PR validation review disposition

Owner: Laurea PR #10, Codex gap-filling-20260915. Review 4022747327.

The review claims GITHUB_TOKEN-created PRs cannot create validation runs and
proposes a new credential or explicit dispatch. Current official GitHub guidance
explicitly includes opened, synchronize and reopened PR events as exceptions:
they create approval-required workflow runs. The existing validate.yml listens
for pull_request with its default activity types and has read-only permissions.

Source checked 2026-09-16:
https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow

Disposition: the no-run premise is contradicted by the current primary source.
Preserve the platform approval gate; do not introduce a credential or dispatch
workaround. Clarify the README with the documented event types and approval UI.

This source disposition is not a protected canary receipt. Actual production
publication, approval, executed validation and merge remain separate outcomes.
The previously verified 110-test source receipt remains valid for unchanged code;
this documentation-only change passes diff hygiene and the validation workflow
passes actionlint. No workflow or publication was invoked.
