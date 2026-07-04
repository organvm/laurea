# r/Python draft (flair: Showcase)

**Title:** I built a zero-dependency Python engine that computes GitHub
"top X%" claims with receipts — and deletes the claim when the data
stops supporting it

**Body:**

**What my project does.** LAVREA snapshots a GitHub identity over
GraphQL (stdlib urllib only — no requests, no click), runs a registry of
`@detector` functions that each measure one axis of output, tiers each
measurement against a conservative percentile floor whose citation lives
in the code next to the threshold, and renders animated SVG cards. A
composite claim renders only as a conjunction of independently-cleared
floors, so it's mathematically a floor itself. A daily Action recomputes
everything; unsupported claims un-render.

**Target audience.** Anyone who wants portfolio/profile stats that
survive scrutiny — job hunters, freelancers, and people who enjoy the
engineering of honesty as much as the bragging.

**Comparison.** github-readme-stats renders your raw numbers; trophy
generators gamify them. LAVREA is the third thing: percentile *claims*
with a methodology doc, conservative-floor logic, and self-deletion —
closer to an instrument than a badge.

Extending it is one function + one cited baseline. MIT.

Repo: https://github.com/4444J99/laurea
