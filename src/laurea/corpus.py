"""Identity-free corpus totals and publication coverage guards."""
from __future__ import annotations

from typing import Any


def require_complete(snapshot: dict[str, Any]) -> None:
    """Reject known incomplete/new malformed coverage before any publication."""
    if "coverage" not in snapshot:
        return  # Legacy unredacted v2 snapshots retain their recorded semantics.
    coverage = snapshot["coverage"]
    if (not isinstance(coverage, dict) or coverage.get("status") != "complete"
            or coverage.get("organization_scope_complete") is not True
            or type(coverage.get("failed_sources")) is not int
            or coverage["failed_sources"] != 0):
        raise ValueError("source coverage is unmeasured; existing published assets and history are preserved")
    if coverage.get("private_repositories_excluded", 0) and "repository_aggregates" not in snapshot:
        raise ValueError("redacted corpus is missing its aggregate evidence")


def aggregate_repositories(repos: list[dict[str, Any]]) -> dict[str, Any]:
    languages: dict[str, int] = {}
    nonfork = 0
    stars = 0
    for repo in repos:
        if (type(repo.get("isFork")) is not bool or type(repo.get("stargazerCount")) is not int
                or repo["stargazerCount"] < 0):
            raise ValueError("repository aggregate fields unavailable")
        stars += repo["stargazerCount"]
        if repo["isFork"]:
            continue
        nonfork += 1
        primary = repo.get("primaryLanguage")
        if primary is not None:
            if not isinstance(primary, dict) or not isinstance(primary.get("name"), str) or not primary["name"]:
                raise ValueError("repository language unavailable")
            language = primary["name"]
            languages[language] = languages.get(language, 0) + 1
    return {"scope": "token_visible", "nonfork_repositories": nonfork,
            "stars": stars, "primary_languages": languages}


def corpus_totals(snapshot: dict[str, Any]) -> dict[str, Any]:
    require_complete(snapshot)
    value = snapshot.get("repository_aggregates")
    if value is None:
        return aggregate_repositories(snapshot["repos"])
    if (not isinstance(value, dict) or value.get("scope") != "token_visible"
            or any(type(value.get(k)) is not int or value[k] < 0 for k in ("nonfork_repositories", "stars"))
            or not isinstance(value.get("primary_languages"), dict)
            or any(not isinstance(k, str) or not k or type(v) is not int or v < 1
                   for k, v in value["primary_languages"].items())
            or sum(value["primary_languages"].values()) > value["nonfork_repositories"]):
        raise ValueError("invalid repository aggregate evidence")
    return value
