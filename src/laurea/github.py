"""Live snapshot collection from the GitHub GraphQL API.

Zero dependencies: urllib only. The token comes from LAUREA_TOKEN,
GH_TOKEN, or GITHUB_TOKEN (first found). Public data is enough for
every axis; a user-scoped token additionally counts private
(restricted) contributions.
"""

from __future__ import annotations

from .corpus import aggregate_repositories

import json
import os
import subprocess
import urllib.request
from typing import Any

GRAPHQL_URL = "https://api.github.com/graphql"

_USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100) { totalCount }
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      restrictedContributionsCount
    }
  }
}
"""

_ORG_REPOS_QUERY = """
query($org: String!, $cursor: String) {
  organization(login: $org) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        nameWithOwner
        isPrivate
        defaultBranchRef { name target { oid } }
        name
        isFork
        isArchived
        stargazerCount
        pushedAt
        primaryLanguage { name }
      }
    }
  }
}
"""

_USER_REPOS_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        nameWithOwner
        isPrivate
        defaultBranchRef { name target { oid } }
        name
        isFork
        isArchived
        stargazerCount
        pushedAt
        primaryLanguage { name }
      }
    }
  }
}
"""


def resolve_token() -> str:
    for var in ("LAUREA_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(var)
        if token:
            return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    raise RuntimeError(
        "No GitHub token found: set LAUREA_TOKEN, GH_TOKEN, or GITHUB_TOKEN."
    )


def _gql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "laurea",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


class CoverageError(RuntimeError):
    """A connection could not establish a complete, stable denominator."""


def _paginate_repos(
    query: str, key_path: list[str], variables: dict[str, Any], token: str
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    cursor: str | None = None
    seen: set[str] = set()
    total: int | None = None
    for _ in range(100):
        conn = _gql(query, {**variables, "cursor": cursor}, token)
        try:
            for key in key_path:
                conn = conn[key]
            count, batch, page = conn["totalCount"], conn["nodes"], conn["pageInfo"]
            if type(count) is not int or count < 0 or not isinstance(batch, list):
                raise CoverageError("malformed connection")
            if total is not None and total != count:
                raise CoverageError("connection changed during collection")
            total = count
            if any(not isinstance(node, dict) for node in batch):
                raise CoverageError("malformed node")
            nodes.extend(batch)
            if type(page["hasNextPage"]) is not bool:
                raise CoverageError("malformed page state")
            if not page["hasNextPage"]:
                if len(nodes) != total:
                    raise CoverageError("connection count mismatch")
                return nodes
            cursor = page["endCursor"]
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise CoverageError("pagination did not advance")
            seen.add(cursor)
        except (KeyError, TypeError) as exc:
            raise CoverageError("unreadable connection") from exc
    raise CoverageError("pagination limit reached")


_ORGS_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    organizations(first: 100, after: $cursor) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { login }
    }
  }
}
"""


def collect(login: str, token: str | None = None) -> dict[str, Any]:
    """Collect visible sources with explicit incomplete and excluded coverage."""
    token = token or resolve_token()
    user = _gql(_USER_QUERY, {"login": login}, token)["user"]
    if not isinstance(user, dict):
        raise ValueError(
            f"GitHub login @{login} is not a user; set LAUREA_LOGIN to a user account"
        )

    failures = 0
    try:
        org_nodes = _paginate_repos(
            _ORGS_QUERY, ["user", "organizations"], {"login": login}, token
        )
        org_logins = [node["login"] for node in org_nodes]
        if any(not isinstance(org, str) or not org for org in org_logins):
            raise CoverageError("malformed organization")
        if len(set(org_logins)) != len(org_logins):
            raise CoverageError("duplicate organization")
        org_scope_complete = True
    except (RuntimeError, ValueError, KeyError, OSError):
        org_logins = []
        org_scope_complete = False
        failures += 1

    repos = []
    visible_repos = []
    private_count = 0
    visibility_unmeasured = 0
    observed_ids: set[str] = set()
    sources = [(_USER_REPOS_QUERY, ["user", "repositories"], {"login": login})]
    sources += [(_ORG_REPOS_QUERY, ["organization", "repositories"], {"org": org})
                for org in org_logins]
    for query, path, variables in sources:
        try:
            batch = _paginate_repos(query, path, variables, token)
            aggregate_repositories(batch)  # Validate before consuming any partial source.
            ids = [repo.get("id") for repo in batch]
            if (any(not isinstance(identity, str) or not identity for identity in ids)
                    or len(set(ids)) != len(ids)
                    or any(type(repo.get("isPrivate")) is not bool for repo in batch)):
                raise CoverageError("malformed repository identity or visibility")
        except (RuntimeError, ValueError, KeyError, OSError):
            failures += 1
            continue
        for repo in batch:
            if repo["id"] in observed_ids:
                continue
            observed_ids.add(repo["id"])
            visible_repos.append(repo)
            if repo["isPrivate"]:
                private_count += 1
                continue
            try:
                current = _gql(
                    "query($id: ID!) { node(id: $id) { ... on Repository { id isPrivate } } }",
                    {"id": repo["id"]}, token,
                ).get("node")
            except (RuntimeError, ValueError, KeyError, OSError, AttributeError, TypeError):
                current = None
            if not isinstance(current, dict) or current.get("id") != repo["id"] or type(current.get("isPrivate")) is not bool:
                visibility_unmeasured += 1
                continue
            if current["isPrivate"]:
                private_count += 1
                continue
            # Reconfirm visibility at the immutable ID before retaining identity.
            repo["health"] = {
                "verification": "unmeasured",
                "security": "unmeasured",
                "pr_readiness": "unmeasured",
            }
            repos.append(repo)

    contrib = user["contributionsCollection"]
    return {
        "login": user["login"],
        "name": user["name"],
        "created_at": user["createdAt"],
        "followers": user["followers"]["totalCount"],
        "orgs": org_logins,
        "repos": repos,
        "repository_aggregates": aggregate_repositories(visible_repos),
        "coverage": {
            "status": "complete" if failures == 0 and visibility_unmeasured == 0 else "unmeasured",
            "scope": "token-visible personal repositories and organization memberships; not an administered-estate census",
            "organization_scope_complete": org_scope_complete,
            "sources_attempted": len(sources) + 1,
            "source_count_scope": "membership discovery and repository connections",
            "failed_sources": failures,
            "observed_repositories": len(observed_ids),
            "public_repositories": len(repos),
            "private_repositories_excluded": private_count,
            "visibility_unmeasured": visibility_unmeasured,
            "archived_public_repositories": sum(repo.get("isArchived") is True for repo in repos),
            "health_status": "unmeasured",
        },
        "contributions": {
            "total": contrib["contributionCalendar"]["totalContributions"],
            "commits": contrib["totalCommitContributions"],
            "pull_requests": contrib["totalPullRequestContributions"],
            "reviews": contrib["totalPullRequestReviewContributions"],
            "issues": contrib["totalIssueContributions"],
            "restricted": contrib["restrictedContributionsCount"],
        },
    }
