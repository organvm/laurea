"""The detector registry — bounded observations over one API snapshot."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .baselines import STATUS_DERIVED, STATUS_MEASURED, status_rank
from .models import Finding

Snapshot = dict[str, Any]
Detector = Callable[[Snapshot], Finding | None]

REGISTRY: list[Detector] = []

# This table classifies GitHub's one primary-language label per repository.
# It describes the visible corpus; it does not prove individual proficiency.
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
    """Register one deterministic observation function."""
    REGISTRY.append(fn)
    return fn


def _validate_snapshot(snapshot: Snapshot) -> None:
    repos = snapshot.get("repos")
    if not isinstance(repos, list) or any(
        not isinstance(repo, dict) or not isinstance(repo.get("isFork"), bool)
        for repo in repos
    ):
        raise ValueError("snapshot.repos must contain complete isFork booleans")
    orgs = snapshot.get("orgs")
    if not isinstance(orgs, list) or any(not isinstance(org, str) for org in orgs):
        raise ValueError("snapshot.orgs must be a list of organization logins")
    contributions = snapshot.get("contributions")
    required = ("total", "commits", "pull_requests", "reviews", "issues", "restricted")
    if not isinstance(contributions, dict) or any(
        not isinstance(contributions.get(key), int) or contributions[key] < 0
        for key in required
    ):
        raise ValueError("snapshot.contributions contains incomplete counts")


def _active_repos(snapshot: Snapshot) -> list[dict[str, Any]]:
    return [repo for repo in snapshot["repos"] if repo["isFork"] is False]


def _langs(snapshot: Snapshot) -> dict[str, int]:
    counts: dict[str, int] = {}
    for repo in _active_repos(snapshot):
        primary = repo.get("primaryLanguage")
        language = primary.get("name") if isinstance(primary, dict) else None
        if isinstance(language, str) and language:
            counts[language] = counts.get(language, 0) + 1
    return counts


@detector
def contributions_year(snapshot: Snapshot) -> Finding:
    contributions = snapshot["contributions"]
    total = contributions["total"]
    return Finding(
        axis="contributions_year",
        title="GitHub contribution activity (12 months)",
        value=float(total),
        unit="contribution events",
        status=STATUS_MEASURED,
        evidence=(
            f"GitHub reports {total:,} contribution-calendar events in the last 12 months "
            f"({contributions['commits']:,} commits, "
            f"{contributions['pull_requests']:,} pull requests, "
            f"{contributions['reviews']:,} reviews, and "
            f"{contributions['issues']:,} issues)"
        ),
        source="GitHub GraphQL contributionsCollection and contributionCalendar",
        analysis=(
            "This is an activity count, not a count of shipped units. GitHub events "
            "vary in scope and do not establish review, merge, quality, or impact."
        ),
    )


@detector
def repos_visible(snapshot: Snapshot) -> Finding:
    count = len(_active_repos(snapshot))
    return Finding(
        axis="repos_visible",
        title="Visible non-fork repository corpus",
        value=float(count),
        unit="repositories",
        status=STATUS_MEASURED,
        evidence=(
            f"{count:,} non-fork repositories were visible across the personal account "
            f"and {len(snapshot['orgs'])} organization memberships returned by the API"
        ),
        source="GitHub GraphQL repositories connections with isFork=false",
        analysis=(
            "Organization repositories can include work by other contributors. "
            "Visibility does not establish individual authorship, maintenance, or operation."
        ),
    )


@detector
def language_breadth(snapshot: Snapshot) -> Finding:
    languages = _langs(snapshot)
    leaders = ", ".join(
        f"{name} ({count})" for name, count in sorted(languages.items(), key=lambda item: -item[1])[:5]
    )
    return Finding(
        axis="language_breadth",
        title="Primary-language breadth of the visible corpus",
        value=float(len(languages)),
        unit="primary-language labels",
        status=STATUS_DERIVED,
        evidence=(
            f"GitHub assigns {len(languages)} distinct primary-language labels across "
            f"the visible non-fork corpus" + (f" — led by {leaders}" if leaders else "")
        ),
        source="Distinct repository.primaryLanguage.name values in the visible corpus",
        analysis=(
            "A repository has one GitHub-assigned primary language. This describes "
            "the corpus and does not establish individual proficiency or authorship."
        ),
    )


@detector
def pull_requests_year(snapshot: Snapshot) -> Finding:
    pull_requests = snapshot["contributions"]["pull_requests"]
    return Finding(
        axis="pull_requests_year",
        title="Pull requests opened (12 months)",
        value=float(pull_requests),
        unit="pull requests",
        status=STATUS_MEASURED,
        evidence=(
            f"GitHub reports {pull_requests:,} pull requests opened in the trailing 12-month collection"
        ),
        source="GitHub GraphQL contributionsCollection.totalPullRequestContributions",
        analysis=(
            "Opened pull requests are activity events; this field does not say whether "
            "they were reviewed, mergeable, merged, distinct in scope, or created without automation."
        ),
    )


@detector
def organization_memberships(snapshot: Snapshot) -> Finding:
    count = len(snapshot["orgs"])
    return Finding(
        axis="organization_memberships",
        title="Visible organization memberships",
        value=float(count),
        unit="organizations",
        status=STATUS_MEASURED,
        evidence=f"GitHub returned {count} organization memberships for this account",
        source="GitHub GraphQL user.organizations (first 20 visible to the token)",
        analysis=(
            "Membership does not by itself establish ownership, administrative authority, "
            "or individual responsibility for every repository in an organization."
        ),
    )


@detector
def language_layer_coverage(snapshot: Snapshot) -> Finding:
    layers = sorted({_LAYERS[language] for language in _langs(snapshot) if language in _LAYERS})
    return Finding(
        axis="language_layer_coverage",
        title="Mapped language-layer coverage",
        value=float(len(layers)),
        unit="mapped layers",
        status=STATUS_DERIVED,
        evidence=(
            f"The static language map places the visible corpus in {len(layers)} layers: "
            f"{', '.join(layers) if layers else 'none'}"
        ),
        source="Deterministic primary-language-to-layer mapping in src/laurea/detectors.py",
        analysis=(
            "This is a corpus classification, not evidence that one person authored, "
            "shipped, or is proficient in every mapped layer."
        ),
    )


@detector
def tenure(snapshot: Snapshot) -> Finding:
    created = datetime.fromisoformat(snapshot["created_at"].replace("Z", "+00:00"))
    years = (datetime.now(timezone.utc) - created).days / 365.25
    return Finding(
        axis="tenure",
        title="Account age",
        value=round(years, 1),
        unit="years",
        status=STATUS_MEASURED,
        evidence=f"The GitHub account was created in {created.year} ({years:.1f} years ago)",
        source="GitHub GraphQL user.createdAt",
        analysis="Account age is not equivalent to continuous professional experience or activity.",
    )


def run_all(snapshot: Snapshot) -> list[Finding]:
    """Validate one snapshot, then return its bounded observations."""
    _validate_snapshot(snapshot)
    findings = [finding for fn in REGISTRY if (finding := fn(snapshot)) is not None]
    findings.sort(key=lambda finding: (status_rank(finding.status), finding.axis))
    return findings
