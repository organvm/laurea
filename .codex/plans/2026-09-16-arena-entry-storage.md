# Arena immutable entrant storage

Owner: Laurea PR #10, concurrency review4023115101.

Add write_entry: one validated activity record per positive issue ID, with timezone-bound observation time. Atomic hard-link publication prevents partially written records and refuses changed evidence at an existing issue path. Identical replay is idempotent. Distinct issue records do not rewrite a shared table. Reject malformed identities, negative/non-integer metrics and symlink destinations.

Seven tests pass: simultaneous distinct entrants, idempotent replay versus changed evidence, invalid IDs/logins, and symlink preservation. This is the storage foundation only; CLI generation, publication scope, table materialization and automatic continuation remain required. Current arena runtime still uses the old table publication path until that integration lands; no concurrency-completion claim is made.
