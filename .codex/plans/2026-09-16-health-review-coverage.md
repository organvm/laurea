# Health review follow-through

Owner: Codex; PR #10.

Review 4022239982: count a currently running step as positive execution evidence and expose in_progress plus active_steps. Queued/skipped steps still do not count as execution. This does not establish workflow success or repository acceptance.

Review 4022250081: runs_unmeasured includes both omitted runs and observed runs with missing job evidence. Pull coverage requires the child row itself to be measured; a closed detail from a previously open listing cannot satisfy the open-PR denominator even when its checks/reviews are readable.

Validation: all 75 tests passed with env PYTHONPATH=src python3 -m pytest -q; diff hygiene passed. New regressions cover active execution, combined omitted/unknown runs, and a consistently closed detail after open listing. Existing publication-preservation and private-aggregate tests remain green. Earlier review dispositions remain recorded in the preceding plan; no runtime, account grant or publication changed.
