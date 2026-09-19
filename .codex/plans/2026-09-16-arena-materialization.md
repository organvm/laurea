# Deterministic arena materialization

Owner: Laurea PR #10. arena-table validates a bounded directory (maximum10,000 records, 10KB each), rejects symlinks/schema/filename mismatches, selects the latest timestamp/issue for repeated logins, and renders all distinct logins with deterministic ties. Validate the complete input before atomic output replacement. Rendering occurs once rather than rewriting/reparsing a growing table per row.

Fourteen arena/entry tests pass, including multi-entrant retention, repeated-login selection, idempotent output, and preservation of an existing table after malformed input. The command has no network or publication effects.

Still required before ready: migrate any valid existing table rows into provenance-bound baseline records without inventing issue identities; connect accepted-record updates to bounded table generation/publication and stale-generation rejection. The PR remains draft; current table materialization is a source capability, not installed automation.
