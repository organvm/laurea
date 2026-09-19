# Arena settlement evidence and human closure boundary

Owner: organvm/laurea PR #10; review 4023513093.

The read-only `arena-table --settlement-report` snapshots bounded inputs, validates the complete table, and reports every observation as represented or superseded_in_table with SHA-256 input bindings. It performs no network access or issue mutation and explicitly labels default acceptance unmeasured. Seventeen arena-entry tests passed in 0.25 seconds, including stale-table rejection, preserved caller bytes, superseded/represented rows, and JSON CLI output.

The global instruction that only the human closes atoms constrains earlier planning language about automatic settlement: row evidence is implemented; automatic issue closure is intentionally not activated. The README now describes record acceptance, table preparation, pending-proposal refresh, local evidence, and human closure separately. Existing issues retain durable ownership rather than being closed at record merge.

Hosted default identity, table adoption, branch enforcement, generated PR execution, and actual issue disposition remain external acceptance evidence. This source report cannot substitute for them. PR #10 remains draft for final review and acceptance reconciliation.
