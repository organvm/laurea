"""Live snapshot collection from the GitHub GraphQL API.

Zero dependencies: urllib only. The token comes from LAUREA_TOKEN,
GH_TOKEN, or GITHUB_TOKEN (first found). Public data is enough for
every axis; a user-scoped token additionally counts private
(restricted) contributions.
"""

from __future__ import annotations

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
    organizations(first: 20) { nodes { login } }
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


def _paginate_repos(
    query: str, key_path: list[str], variables: dict[str, Any], token: str
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        data = _gql(query, {**variables, "cursor": cursor}, token)
        conn = data
        for key in key_path:
            conn = conn[key]
        nodes.extend(conn["nodes"])
        page = conn["pageInfo"]
        if not page["hasNextPage"]:
            return nodes
        cursor = page["endCursor"]


def collect(login: str, token: str | None = None) -> dict[str, Any]:
    """Collect the full identity snapshot: user, orgs, every owned repo."""
    token = token or resolve_token()
    user = _gql(_USER_QUERY, {"login": login}, token)["user"]

    repos = _paginate_repos(
        _USER_REPOS_QUERY, ["user", "repositories"], {"login": login}, token
    )
    org_logins = [n["login"] for n in user["organizations"]["nodes"]]
    for org in org_logins:
        try:
            repos.extend(
                _paginate_repos(
                    _ORG_REPOS_QUERY, ["organization", "repositories"], {"org": org}, token
                )
            )
        except RuntimeError:
            # An org the token cannot read fully still counts as operated;
            # its repos simply don't enter the measured corpus.
            continue

    contrib = user["contributionsCollection"]
    return {
        "login": user["login"],
        "name": user["name"],
        "created_at": user["createdAt"],
        "followers": user["followers"]["totalCount"],
        "orgs": org_logins,
        "repos": repos,
        "contributions": {
            "total": contrib["contributionCalendar"]["totalContributions"],
            "commits": contrib["totalCommitContributions"],
            "pull_requests": contrib["totalPullRequestContributions"],
            "reviews": contrib["totalPullRequestReviewContributions"],
            "issues": contrib["totalIssueContributions"],
            "restricted": contrib["restrictedContributionsCount"],
        },
    }
