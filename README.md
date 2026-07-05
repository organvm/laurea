# LAVREA — the laurels are computed

**An evidence-backed excellence engine.** Nobody sells us for us — so this
repo does it with data. LAVREA snapshots a GitHub identity (every org,
every repo, every contribution), runs a registry of detectors that each
measure one axis of engineering output, assigns each measurement a
**conservative percentile floor** from cited population baselines, and
renders only the claims the data supports — as animated SVG laurels that
recompute themselves daily.

<p align="center">
  <img src="assets/cards/hero.svg" alt="hero laurel" width="800"/>
</p>

<p align="center">
  <img src="assets/cards/contributions_year.svg" alt="contributions" width="420"/>
  <img src="assets/cards/repos_owned.svg" alt="portfolio" width="420"/>
</p>
<p align="center">
  <img src="assets/cards/language_breadth.svg" alt="languages" width="420"/>
  <img src="assets/cards/full_stack_coverage.svg" alt="full stack" width="420"/>
</p>

The full generated report: **[SUPERLATIVES.md](assets/SUPERLATIVES.md)** ·
The honesty contract: **[METHODOLOGY.md](METHODOLOGY.md)**

## The verdict meter

Output is what you ship; the verdict is what the world does about it.
LAVREA also records the *reception* signals (stars, followers, traffic)
as a daily time series and renders them with deltas — so the verdict is
a chart, not a feeling:

<p align="center">
  <img src="assets/cards/verdict.svg" alt="verdict meter" width="420"/>
</p>

## Run it on yourself in 60 seconds

1. **[Use this template](../../generate)** (or fork).
2. Enable Actions on your copy. That's it — the workflow detects the
   repo owner and computes *your* laurels daily; only the claims *your*
   data supports will render.
3. Optional: add a `LAUREA_TOKEN` repo secret (a classic PAT) so private
   org membership and restricted contributions count too.
4. Embed the cards anywhere:
   `https://raw.githubusercontent.com/YOU/laurea/main/assets/cards/hero.svg`

## How the claim actually works — and what it is

Anyone can put "top 1%" in a bio. LAVREA makes it a **theorem with
measured premises** — and scopes it honestly: the composite classifies a
top-1% *output profile* (scale, breadth, operational complexity — the
orchestration skillset: architecture, decomposition, specification,
verification, integration), not a universal
ranking of ability. Quality, correctness, and adoption are different
questions needing different evidence; the report renders what it does
*not* establish right next to what it does.

1. Each axis (contribution volume, portfolio size, language breadth,
   integration throughput…) is measured exactly, from the live API.
2. Each measurement is tiered against a **floor deliberately set far
   above the cited population statistic** — so the rendered tier is at
   most as strong as reality.
3. The headline composite ("top 1% Python full-stack engineer") is a
   **conjunction**: it renders only if *every* leg independently clears
   its top-1% floor *and* Python leads the shipped corpus *and* the code
   spans 4+ stack layers. A conjunction of top-1% conditions is at most
   as common as its rarest member — the composite is therefore itself a
   floor.
4. It recomputes daily. If the output stops, **the claim deletes
   itself.** That is the difference between a boast and an instrument.

## Use it on yourself

```bash
pip install -e '.[test]'
laurea run --login YOUR_LOGIN     # compute + render into assets/
laurea axes                       # list every detector
python -m pytest tests -q
```

Zero runtime dependencies — stdlib only. Add an axis by writing one
function in [`src/laurea/detectors.py`](src/laurea/detectors.py) and
decorating it with `@detector`; add a baseline (with its citation) in
[`src/laurea/baselines.py`](src/laurea/baselines.py). The GitHub Action
([`laurea.yml`](.github/workflows/laurea.yml)) re-runs the tests, then
recomputes and commits the laurels every day.

## License

MIT.
