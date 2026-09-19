# Organization repository counter reconciliation

Owner: Laurea PR #10, Codex gap-filling-20260915.

For every active-admin organization, compare its GraphQL owned-repository total against REST public plus total-private counters, with before/after stable counter and identity reads. All ten match: 296 organization repositories, 228 public plus 68 private. The alternate owned-private counter sums to 67 and is not substituted for total-private.

Personal GraphQL owned inventory reports 30, yielding the same combined visible total of 326. The authenticated personal REST response omits private counters, so personal completeness cannot be established by counter reconciliation. Keep that observation unmeasured; do not widen credentials or infer completeness from matching historical totals.

Receipt: docs/receipts/organization-counter-reconciliation-20260916.json. Only aggregate counts are retained. This narrows inventory coverage uncertainty but does not establish health, security coverage, deployed enforcement, or any private repository outcome.
