# Show HN draft

**Title:** Show HN: LAVREA – GitHub brag cards that delete themselves when the data stops supporting them

**Body:**

Anyone can put "top 1%" in a bio, so I built the opposite of a bio: an
engine that measures my GitHub output exactly (contributions, PRs, owned
repos, language breadth, stack coverage), tiers each axis against a
conservative population floor with the citation next to the number, and
only renders a claim when the data clears the bar.

The headline claim is a conjunction — every leg has to hold
simultaneously, so P(A∧B∧C∧D) ≤ min of the legs and the rendered tier is
a floor, not an estimate. It recomputes daily in CI; the day my output
drops below a floor, the card deletes itself. My favorite bug report so
far: the default Actions token couldn't see my private org memberships,
the snapshot collapsed, and the composite claim silently removed itself
— the honesty mechanism firing was the feature working.

Zero runtime dependencies (stdlib only), animated SVGs, MIT. Fork it,
enable Actions, and it computes *your* laurels — only the claims your
data supports will render, which for most of us is the point.

Repo: https://github.com/4444J99/laurea
Methodology: https://github.com/4444J99/laurea/blob/main/METHODOLOGY.md

**Notes for the send:** post 8–10am ET Tue–Thu; first comment should be
the METHODOLOGY summary + the token-collapse anecdote; answer every
comment in the first 3 hours.
