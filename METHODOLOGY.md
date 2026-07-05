# METHODOLOGY — the honesty contract

## 0. Scope: what kind of claim this is

LAVREA classifies a measured **output profile** — the scale, breadth, and
operational complexity of shipped GitHub work. It is a rule-based,
reproducible descriptor, not a peer-reviewed ranking of engineering
ability. Contribution volume at this scale measures *orchestration* —
architecture, decomposition, specification, verification, integration
across an automated, agent-amplified development system — rather than
typing speed. That is disclosed here, in the fine print, because an
instrument that hides its era stops being an instrument. It says
nothing about code
quality, correctness, reliability, adoption, or impact, which require
different evidence. Every generated report renders that negative space
explicitly ("What these numbers do not establish").

A percentile claim is only worth what its weakest assumption is worth.
LAVREA's rendering pipeline is therefore built around four rules:

## 1. Measurements are exact; only baselines are estimated

Every `value` in `assets/metrics.json` comes verbatim from the GitHub
GraphQL API at compute time: contribution calendar totals, repository
counts across the user and every operated organization, primary
languages of owned non-fork repositories. Forks are excluded from the
portfolio. Nothing is self-reported.

## 2. Percentiles are floors, never point estimates

GitHub does not publish per-user percentile tables, so no honest tool
can print "you are P99.63". What *is* defensible is a **floor**: a
threshold set far enough above the cited population statistic that the
tier holds even under pessimistic assumptions. Examples:

- **Contributions/yr ≥ 5,000 → "top 1%".** GitHub reported 100M+
  accounts (Octoverse 2023), the large majority dormant in any given
  year. 5,000/yr is ~14 shipped units of work every day of the year —
  a behavior rare even among *active* developers, which is the harder
  comparison class and the one the floor is set against. 20,000/yr
  (≥55/day) approaches the entry range of public national contribution
  leaderboards → "top 0.1%" floor.
- **Owned repos ≥ 50 → "top 1%".** The median account owns 0–2 public
  repositories; public GH Archive analyses put >30 owned repos in the
  top percentile. 200+ → "top 0.1%" floor.
- **Language breadth ≥ 10 primary languages → "top 1%".** Octoverse
  language data shows typical developers ship in 1–3 languages. Only a
  language that *leads at least one shipped repository* counts.

Each `Baseline` in `src/laurea/baselines.py` carries its `source` and
`method` in code, next to the numbers, where a PR can challenge them.

## 3. The composite claim is a conjunction, so it is also a floor

"Top 1% Python full-stack engineer" renders **only** when all legs hold
simultaneously:

- contribution volume clears its top-1% floor, **and**
- portfolio size clears its top-1% floor, **and**
- Python is the plurality language of the shipped corpus, **and**
- shipped code leads in ≥4 distinct stack layers (frontend, backend,
  infra, native, creative).

P(A ∧ B ∧ C ∧ D) ≤ min(P(A), …, P(D)) — the population satisfying the
conjunction is at most as large as the population satisfying its rarest
leg, so the composite tier inherits the per-leg floor. If any leg fails
on any given day, `composite_python_full_stack` returns `None` and the
headline claim deletes itself from the rendered assets.

## 4. Claims expire with their data

The GitHub Action recomputes daily against the live API and commits the
diff. The laurels are a *projection of current output*, not a plaque.
Anyone can re-run `laurea run --login 4444J99` and get the same numbers
from the same public API.

## Known limitations (stated, not hidden)

- Contribution totals depend on the token: a user PAT counts private
  (restricted) contributions; the default Actions token measures the
  public estate only. Either way the floors are applied to what was
  actually measured.
- "Stack layer" mapping is a fixed language→layer table in
  `detectors.py`; it undercounts (a Python repo that contains a React
  frontend counts once, as backend) — an undercount keeps the floor
  conservative.
- Baseline citations are population-level reports, not a random sample
  of "engineers"; floors are set with wide margins precisely because of
  that looseness. Tighter public data would allow tighter floors — PRs
  welcome.
