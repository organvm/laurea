# Final visibility readback before health disclosure

Owner: Laurea PR #10, Codex gap-filling-20260915. Addresses review 4022675382.

Keep a pristine redacted result until the final repository read confirms public visibility and the same exact integer repository ID. Perform this read after default-head readback. On private, unknown, unavailable, malformed or changed-identity evidence, return only the redacted report, preserving requested-scope denominators and confirmed private exclusion counts. Remove collected identity, SHA, verification, security and PR details together.

Validation: env PYTHONPATH=src python3 -m pytest -q reports 110 passed in 6.21 seconds; diff hygiene passes. Five added cases cover visibility loss and readback failure. No public or private repository state is mutated by this change. This is source privacy enforcement, not deployed health acceptance.

Review 4022667028 compares historical test counts with another tree. Earlier 72, 75, 92 and 105 receipts describe their own source generations; they are not rewritten to current counts. Current full execution is 110.
