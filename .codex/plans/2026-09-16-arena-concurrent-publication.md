# Arena concurrent publication acceptance

Owner: Laurea PR #10; review4023115101 remains substantive and unresolved.

Current evidence: arena.yml groups runs by issue number; publish.py creates a unique automation/arena/run-attempt branch, permits source to be an ancestor of current default, and stages the entire LEADERBOARD.md. Two issues can therefore prepare independent whole-table replacements. A global concurrency group alone serializes run execution but does not coordinate still-open PRs. No production publication is accepted while this remains unresolved.

Required implementation: preserve entrant observations as independently identified records or reconcile all pending entrants through a single owned update transaction; bind generated table to the complete entrant set and current default generation. Preserve each issue obligation and exact owner when a predecessor is pending. Provide a bounded automatic continuation after predecessor integration, without replaying publication on ambiguous outcomes or force-pushing branches. Do not silently drop a newer row during conflict resolution.

Acceptance tests: two simultaneous issues both survive into the eventual table; an unmerged predecessor remains explicit; base movement invalidates stale table output; failed/ambiguous publication produces no duplicate; pending issue obligations resume after predecessor integration; malformed or private-source inputs remain fail-closed. Existing unique-branch and no-default-write invariants remain required.

Next command for source work: inspect src/laurea/arena.py and tests/test_publish.py, then implement the smallest record-preserving update design across arena and publisher with fake-GitHub plus local-Git integration fixtures. This plan does not count as implemented concurrency control.
