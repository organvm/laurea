# Issue-bound arena publication

Owner: Laurea PR #10. Workflow passes its source issue number to the CLI. Arena publisher admits only arena/entries/ISSUE.json, validates schema/issue, bounded file size, row values and timestamp, and rejects symlinks and unrelated paths before Git mutation. A record PR closes its source issue only when its observation lands. Distinct entrants no longer replace the shared leaderboard file.

Validation: 24 publication/entry tests passed, including isolated actual Git pushes and rejection of another issue record or a whole-table diff. Arena workflow actionlint and diff hygiene passed. Table materialization from accepted records remains required; no current workflow run was invoked. Do not merge this unfinished concurrency tranche until its deterministic table-generation continuation is integrated and verified.
