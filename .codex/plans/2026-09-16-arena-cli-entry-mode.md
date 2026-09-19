# Arena CLI issue records

Owner: Laurea PR #10. Add arena --issue POSITIVE_ID --entries DIRECTORY to write the immutable observation record. This mode does not modify LEADERBOARD.md. Invalid issue IDs fail before API collection. Existing local table mode is preserved for compatibility until the publication integration is complete.

Twelve entry/arena tests pass, including a CLI regression that proves an existing table remains byte-identical while the requested issue record is created. Publication workflow still uses the old mode; the next source step is to constrain publish(arena) to exactly the event-owned issue record, then switch the workflow and implement deterministic table materialization from accepted records. Do not treat this additive CLI path as runtime concurrency completion.
