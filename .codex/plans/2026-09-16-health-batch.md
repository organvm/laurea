# Bounded health over an explicit inventory

Owner: Laurea PR #10, Codex gap-filling-20260915.

Add health-batch with a unique declared OWNER/NAME inventory and a bounded 1..20 inspection limit. Share one Reader request/time budget across the entire batch. Keep inventory entries, attempted entries, unattempted entries, confirmed private exclusions, unknown attempts and duplicate observed stable identities separate. Never claim inventory completeness or health acceptance from supplied names or successful collection. Reuse final public-readback redaction in each child report.

Validation: all 118 tests pass in 6.14 seconds, including denominator preservation, malformed/duplicate inventory rejection, private redaction, budget failure, one shared Reader and CLI exit 77. Documentation explains the scope and limit. This is read-only collection, not relay profile execution or enforcement activation.
