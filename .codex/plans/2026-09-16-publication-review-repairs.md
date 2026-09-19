# Publication review repairs

Owner: Laurea PR #10. Address findings 4023777360, 4023777372 and 4023777353.
Reconfirm public visibility at stable repository identity; redact unavailable or
changed identities while retaining identity-free aggregates and unknown coverage.
Bind unchanged refresh trees to advanced source commits. Trigger table preparation
on any push while retaining the actual-default-branch job guard.

Verify collection privacy and real-Git publication regressions, full repository
tests, actionlint and diff hygiene. Hosted admission and live publication remain
separate; do not invoke production publishers during verification.

Verification: 131 tests outside test_publish.py pass on the final source tree;
the unchanged publication shard passed in the earlier 44-test focused batch.
Malformed visibility responses are covered and remain identity-free/unmeasured.
Actionlint and git diff --check pass. The prior remaining-tests process handle
was unavailable; its result is not counted as evidence.
