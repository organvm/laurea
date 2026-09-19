# Arena automatic table publisher

Owner: organvm/laurea PR #10 (draft).

The new arena-table workflow renders accepted records and the preserved baseline after main pushes, then prepares a unique PR through the existing publisher. Manual workflow invocation is available; none was invoked in this session. Runs have a ten-minute bound and serialized publication group. Every main push provides continuation after observation integration; a table-only merge renders unchanged output and creates no further PR.

The arena-table publication kind permits only LEADERBOARD.md changes, validates full materialization, requires source SHA equal current default SHA, and reads the default again after validation. Existing branch/PR readbacks and ambiguity handling apply. It never pushes the default, force-updates a branch, closes entrant issues, or merges.

Validation: 21 publication tests passed in 9.59 seconds; actionlint for arena-table and validate workflows and git diff --check passed. Tests include unique-branch publication, default preservation, moved-default rejection, and incomplete-render rejection before push.

Remaining integration: reconcile an older open table PR without proliferating competing proposals; validate movement between generation and merge through the owning merge rail; exercise two independently integrated entrants end to end. GitHub token workflow admission, branch enforcement, hosted execution, and runtime adoption are not established by these local tests. Keep PR #10 draft.
