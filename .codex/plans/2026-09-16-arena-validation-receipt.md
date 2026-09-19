# Arena validation and continuation

Owner: organvm/laurea PR #10 (draft), branch fix/explicit-source-coverage-20260916.

The materializer is pushed at e96d6cd000c44a284af188bc112e701488b71ba6. The accompanying publisher correction rejects boolean schema versions, extra envelope fields, and non-object records before staging or pushing; caller bytes are preserved.

Validation on the combined source tree: `PYTHONPATH=src python3 -m pytest -q`: 139 passed in 8.09 seconds. `actionlint .github/workflows/arena.yml` and `git diff --check`: exit 0. These are local source receipts, not hosted execution or adoption.

Remaining acceptance for review 4023115101: preserve the existing 4444J99 row (verified date 2026-08-21) with explicit historical source provenance, without inventing an issue identity or precise observation timestamp; add bounded post-merge table generation with source-generation binding and stale-result rejection; verify concurrent record integrations retain both entrants in the final derived table. The current CLI materializer must not replace the live table until baseline preservation and continuation are implemented. PR #10 remains draft. No integration submission was made for this head.
