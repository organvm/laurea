"""Cited population baselines and the conservative-floor tier logic.

The honesty contract of LAVREA lives in this file:

* Every threshold below is a **floor**, deliberately set far above the
  cited population statistic, so a rendered tier is *at most* as strong
  as reality — never stronger.
* Every baseline names its source. If a source cannot be named, the
  axis renders as "notable" (no percentile claim).
* GitHub reported **100M+ developer accounts** (Octoverse 2023); the
  large majority are dormant in any given year. Floors here are chosen
  to hold even against the *active* subpopulation, which is the harder
  comparison — that is what makes the floors safe.
"""

from __future__ import annotations

from dataclasses import dataclass

TIER_TOP_01 = "top 0.1%"
TIER_TOP_1 = "top 1%"
TIER_TOP_5 = "top 5%"
TIER_NOTABLE = "notable"

# Ordered strongest → weakest so the first cleared floor wins.
_TIER_ORDER = (TIER_TOP_01, TIER_TOP_1, TIER_TOP_5, TIER_NOTABLE)


@dataclass(frozen=True)
class Baseline:
    axis: str
    # (threshold, tier) pairs, descending by threshold.
    floors: tuple[tuple[float, str], ...]
    source: str
    method: str

    def tier_for(self, value: float) -> str:
        for threshold, tier in self.floors:
            if value >= threshold:
                return tier
        return TIER_NOTABLE


BASELINES: dict[str, Baseline] = {
    "contributions_year": Baseline(
        axis="contributions_year",
        floors=((20_000, TIER_TOP_01), (5_000, TIER_TOP_1), (1_500, TIER_TOP_5)),
        source=(
            "GitHub Octoverse 2023 (100M+ accounts, majority dormant per year); "
            "public country leaderboards (gayanvoice/top-github-users) where "
            "national top-1000 entry sits in the low five figures of yearly "
            "contributions"
        ),
        method=(
            "5,000 contributions/year is ~14 shipped units of work every day "
            "of the year. Even restricted to active developers, sustained "
            "daily double-digit output is a top-1% behavior; 20,000/year "
            "approaches national-leaderboard territory, hence the 0.1% floor."
        ),
    ),
    "repos_owned": Baseline(
        axis="repos_owned",
        floors=((200, TIER_TOP_01), (50, TIER_TOP_1), (20, TIER_TOP_5)),
        source=(
            "GitHub Octoverse account totals vs. repository totals: the "
            "median account owns 0–2 public repositories; multiple public "
            "analyses of the GH Archive corpus put >30 owned repos in the "
            "top percentile of accounts"
        ),
        method=(
            "Counts repositories owned across the user and every organization "
            "they operate. 200+ maintained repositories is an institutional "
            "footprint, not a hobbyist one."
        ),
    ),
    "language_breadth": Baseline(
        axis="language_breadth",
        floors=((10, TIER_TOP_1), (6, TIER_TOP_5)),
        source=(
            "Octoverse language reports: the typical developer ships in 1–3 "
            "languages; polyglot activity beyond 5 primary languages across "
            "owned repos is rare in GH Archive analyses"
        ),
        method=(
            "Counts distinct primary languages across owned, non-fork "
            "repositories. Only languages that lead at least one shipped "
            "repository count — reading a language is not shipping it."
        ),
    ),
    "pull_requests_year": Baseline(
        axis="pull_requests_year",
        floors=((2_000, TIER_TOP_01), (500, TIER_TOP_1), (150, TIER_TOP_5)),
        source=(
            "Octoverse pull-request volume statistics; median active "
            "developer opens well under 100 PRs/year"
        ),
        method=(
            "PRs are integration events — each one is a reviewed, mergeable "
            "unit. 500/year is ~10 every week without pause."
        ),
    ),
    "orgs_operated": Baseline(
        axis="orgs_operated",
        floors=((8, TIER_TOP_1), (3, TIER_TOP_5)),
        source=(
            "GitHub organization membership statistics: most accounts belong "
            "to 0–1 organizations and *operate* none"
        ),
        method=(
            "Counts organizations the user operates (member with owned "
            "repositories in the federation). Operating a multi-org "
            "architecture is system design, not account usage."
        ),
    ),
}


# Human translation of a floor: what the tier means as odds. Floors, so "at least".
TIER_ODDS = {
    TIER_TOP_01: "at least 1 in 1,000",
    TIER_TOP_1: "at least 1 in 100",
    TIER_TOP_5: "at least 1 in 20",
}


def odds_for(tier: str) -> str | None:
    return TIER_ODDS.get(tier)


def tier_rank(tier: str) -> int:
    """Lower is stronger; useful for sorting findings by strength."""
    return _TIER_ORDER.index(tier)
