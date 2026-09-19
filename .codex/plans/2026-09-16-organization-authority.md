# Stable organization authority comparison

Owner: Laurea PR #10, Codex gap-filling-20260915.

Compare the authenticated active-admin membership roster against paginated GraphQL organization discovery by stable node ID, not counts or names. The authenticated actor matches the requested user. All ten IDs match; zero discovered organizations lack admin evidence and zero admin organizations are missing from discovery. Publish only aggregate results in docs/receipts/organization-authority-20260916.json.

This closes the membership-set ambiguity from the previous visible-source receipt. It does not establish repository-level token visibility or health. A sampled organization REST response exposes public_repos and two different private counters; those counters must be interpreted and compared across the entire scope before treating the visible repository count as unrestricted inventory. No account settings, repository metadata or generated publication was changed.
