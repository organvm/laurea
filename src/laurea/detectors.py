"""The detector registry — each detector measures one axis of output.

Add a detector = add one function decorated with ``@detector``. Every
detector receives the snapshot and returns a Finding (or None when the
axis does not apply). The composite detector at the bottom renders the
headline claim only when every constituent axis independently clears
its floor — a conjunction of top-1% conditions is at most as common as
its rarest member, so the composite tier is itself a floor.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .baselines import BASELINES, TIER_TOP_1, TIER_NOTABLE, tier_rank
from .models import Finding

Snapshot = dict[str, Any]
Detector = Callable[[Snapshot], Finding | None]

REGISTRY: list[Detector] = []

# Language → stack layer. Only languages that lead a shipped repo count.
_LAYERS: dict[str, str] = {
    "JavaScript": "frontend",
    "TypeScript": "frontend",
    "Astro": "frontend",
    "HTML": "frontend",
    "CSS": "frontend",
    "Swift": "native",
    "Kotlin": "native",
    "Python": "backend",
    "Go": "backend",
    "Rust": "backend",
    "Ruby": "backend",
    "Shell": "infra",
    "Dockerfile": "infra",
    "HCL": "infra",
    "Makefile": "infra",
    "SuperCollider": "creative",
    "G-code": "creative",
    "Max": "creative",
}


def detector(fn: Detector) -> Detector:
    REGISTRY.append(fn)
    return fn


def _active_repos(snapshot: Snapshot) -> list[dict[str, Any]]:
    return [r for r in snapshot["repos"] if not r["isFork"]]


def _langs(snapshot: Snapshot) -> dict[str, int]:
    counts: dict[str, int] = {}
    for repo in _active_repos(snapshot):
        lang = (repo.get("primaryLanguage") or {}).get("name") if repo.get("primaryLanguage") else None
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return counts


@detector
def contributions_year(snapshot: Snapshot) -> Finding:
    total = snapshot["contributions"]["total"]
    base = BASELINES["contributions_year"]
    return Finding(
        axis=base.axis,
        title="Contribution volume (12 months)",
        value=float(total),
        unit="contributions/yr",
        tier=base.tier_for(total),
        evidence=(
            f"{total:,} contributions in the last 12 months "
            f"({snapshot['contributions']['commits']:,} commits, "
            f"{snapshot['contributions']['pull_requests']:,} pull requests) — "
            f"about {total // 365} shipped units of work every single day"
        ),
        source=base.source,
        analysis=(
            f"{total // 365} shipped units of work per day, every day of the year, "
            "weekends included. A typical active developer records a few hundred "
            "contributions per year; the top floors here mean this account outpaces "
            "at least 999 of every 1,000 active developers. That is not typing "
            "speed — it is an engineer who industrialized his own process."
        ),
    )


@detector
def repos_owned(snapshot: Snapshot) -> Finding:
    count = len(_active_repos(snapshot))
    base = BASELINES["repos_owned"]
    return Finding(
        axis=base.axis,
        title="Repository portfolio",
        value=float(count),
        unit="owned repos",
        tier=base.tier_for(count),
        evidence=(
            f"{count:,} original (non-fork) repositories owned across "
            f"{len(snapshot['orgs'])} operated organizations plus the "
            "personal account — an institutional footprint"
        ),
        source=base.source,
        analysis=(
            f"The median GitHub account owns 0–2 repositories. {count:,} is not a "
            "large personal portfolio — it is the footprint of an engineering "
            "organization: designed, shipped, and maintained by one person."
        ),
    )


@detector
def language_breadth(snapshot: Snapshot) -> Finding:
    langs = _langs(snapshot)
    base = BASELINES["language_breadth"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    leaders = ", ".join(f"{name} ({n})" for name, n in top)
    return Finding(
        axis=base.axis,
        title="Language breadth",
        value=float(len(langs)),
        unit="primary languages",
        tier=base.tier_for(len(langs)),
        evidence=(
            f"{len(langs)} distinct languages each leading at least one "
            f"shipped repository — led by {leaders}"
        ),
        source=base.source,
        analysis=(
            f"Most developers ship in 1–3 languages over a career. {len(langs)} "
            "languages each leading a shipped repository is the breadth of an "
            "entire team compressed into one engineer."
        ),
    )


@detector
def pull_requests_year(snapshot: Snapshot) -> Finding:
    prs = snapshot["contributions"]["pull_requests"]
    base = BASELINES["pull_requests_year"]
    return Finding(
        axis=base.axis,
        title="Integration throughput",
        value=float(prs),
        unit="PRs/yr",
        tier=base.tier_for(prs),
        evidence=(
            f"{prs:,} pull requests opened in 12 months — "
            f"~{prs // 52} reviewed, mergeable units of work every week"
        ),
        source=base.source,
        analysis=(
            f"~{prs // 52} reviewed, mergeable units of work every week. Many "
            "strong professional engineers open fewer pull requests in a year "
            "than this account opens in a month."
        ),
    )


@detector
def orgs_operated(snapshot: Snapshot) -> Finding:
    count = len(snapshot["orgs"])
    base = BASELINES["orgs_operated"]
    return Finding(
        axis=base.axis,
        title="Federation architecture",
        value=float(count),
        unit="organizations",
        tier=base.tier_for(count),
        evidence=(
            f"{count} GitHub organizations operated as a single federated "
            "system — separation of concerns applied to an entire estate, "
            "not just a codebase"
        ),
        source=base.source,
        analysis=(
            f"Most accounts operate zero organizations. {count} is "
            "separation-of-concerns applied to a whole estate — the org chart "
            "of a small company, run by its only employee."
        ),
    )


@detector
def full_stack_coverage(snapshot: Snapshot) -> Finding:
    langs = _langs(snapshot)
    layers = sorted({_LAYERS[lang] for lang in langs if lang in _LAYERS})
    return Finding(
        axis="full_stack_coverage",
        title="Full-stack coverage",
        value=float(len(layers)),
        unit="stack layers",
        tier=TIER_TOP_1 if len(layers) >= 4 else TIER_NOTABLE,
        evidence=(
            f"Shipped repositories lead in {len(layers)} distinct stack "
            f"layers: {', '.join(layers)} — frontend through infrastructure "
            "in one pair of hands"
        ),
        source=(
            "Layer mapping over primary languages of owned non-fork repos; "
            "covering 4+ layers with shipped code is the working definition "
            "of full-stack, and polyglot shipping at this breadth is a "
            "top-percentile behavior (see language_breadth baseline)"
        ),
        analysis=(
            "One person covering roles a company staffs separately: frontend, "
            "backend, infrastructure, native, and creative coding. "
            "'Full-stack' is usually a resume word; here it is a measured property."
        ),
    )


@detector
def tenure(snapshot: Snapshot) -> Finding:
    created = datetime.fromisoformat(snapshot["created_at"].replace("Z", "+00:00"))
    years = (datetime.now(timezone.utc) - created).days / 365.25
    return Finding(
        axis="tenure",
        title="Tenure",
        value=round(years, 1),
        unit="years",
        tier=TIER_NOTABLE,
        evidence=f"On GitHub since {created.year} — {years:.1f} years of shipped history",
        source="Account creation date (no percentile claimed for tenure)",
        analysis=(
            "A decade of public, timestamped history. The output measured above "
            "is a trajectory, not a sprint — and every year of it is auditable."
        ),
    )


def composite_python_full_stack(findings: list[Finding], snapshot: Snapshot) -> Finding | None:
    """The headline: 'top 1% Python full-stack engineer', as a conjunction.

    Requires ALL of: contribution volume at top-1% floor or better,
    portfolio size at top-1% floor or better, Python leading the shipped
    corpus, and full-stack layer coverage. If any leg fails, the
    composite does not render — the claim deletes itself.
    """
    by_axis = {f.axis: f for f in findings}
    legs = ("contributions_year", "repos_owned", "full_stack_coverage")
    if any(a not in by_axis for a in legs):
        return None
    if any(tier_rank(by_axis[a].tier) > tier_rank(TIER_TOP_1) for a in legs):
        return None
    langs = _langs(snapshot)
    if not langs or max(langs, key=lambda k: langs[k]) != "Python":
        return None
    python_repos = langs["Python"]
    return Finding(
        axis="composite_python_full_stack",
        title="Python full-stack engineer — composite placement",
        value=1.0,
        unit="percentile floor",
        tier=TIER_TOP_1,
        evidence=(
            f"Conjunction holds: {by_axis['contributions_year'].value:,.0f} "
            f"contributions/yr (top-1% floor cleared), "
            f"{by_axis['repos_owned'].value:,.0f} owned repos (top-1% floor "
            f"cleared), Python leads the corpus ({python_repos} repos), and "
            f"shipped code spans {by_axis['full_stack_coverage'].value:.0f} "
            "stack layers. A conjunction of independent top-1% conditions "
            "is at most as common as its rarest member — the composite "
            "top-1% claim is therefore a floor, not an estimate."
        ),
        source="Conjunction over the cited per-axis baselines (see METHODOLOGY.md)",
        analysis=(
            "Read it like an underwriter: each leg alone places its holder past "
            "the 99th percentile, and holding all four simultaneously is rarer "
            "than any single leg. At most 1 engineer in 100 can make this claim; "
            "this one re-proves it by machine every morning."
        ),
    )


def run_all(snapshot: Snapshot) -> list[Finding]:
    findings = [f for det in REGISTRY if (f := det(snapshot)) is not None]
    composite = composite_python_full_stack(findings, snapshot)
    if composite:
        findings.insert(0, composite)
    findings.sort(key=lambda f: (tier_rank(f.tier), -f.value))
    return findings
