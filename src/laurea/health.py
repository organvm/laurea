"""Bounded, read-only repository health observations at one default generation.

Executed Actions evidence is distinct from the repository acceptance predicate.
Permission failures and truncated pages stay unmeasured; alert details stay private.
"""
from __future__ import annotations

import json
from copy import deepcopy
import re
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote

from .pulls import collect_pulls
from .security import summarize_alerts


class Unmeasured(RuntimeError):
    """A bounded observation could not establish the requested fact."""


class Reader:
    def __init__(self, token: str, *, seconds: float = 60, requests: int = 40):  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
        self.token = token  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
        self.deadline = time.monotonic() + seconds
        self.remaining = requests

    def __call__(self, path: str) -> Any:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0 or self.remaining <= 0:
            raise Unmeasured("read budget exhausted")
        self.remaining -= 1
        request = urllib.request.Request(
            "https://api.github.com" + path,
            headers={"Authorization": "bearer " + self.token,
                     "Accept": "application/vnd.github+json", "User-Agent": "laurea",
                     "X-GitHub-Api-Version": "2026-03-10"},
        )
        with urllib.request.urlopen(request, timeout=min(10, remaining)) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise Unmeasured("response limit exceeded")
        return json.loads(raw)


def _connection(value: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise Unmeasured("malformed connection")
    nodes = value.get(key)
    count = value.get("total_count")
    if (not isinstance(nodes, list) or type(count) is not int
            or count != len(nodes) or any(not isinstance(n, dict) for n in nodes)):
        raise Unmeasured("incomplete connection")
    return nodes


def _unknown() -> dict[str, Any]:
    return {"status": "unmeasured"}


def _verification(read: Callable, prefix: str, sha: str) -> dict[str, Any]:
    runs = _connection(read(prefix + "/actions/runs?head_sha=" + sha + "&per_page=100"), "workflow_runs")
    observations = []
    # A bounded subset remains explicit; successful children never cover omitted runs.
    for run in runs[:10]:
        if run.get("head_sha") != sha or type(run.get("id")) is not int:
            raise Unmeasured("run generation mismatch")
        row = {"run_id": run["id"], "head_sha": sha,
               "conclusion": run.get("conclusion"), "execution": "unmeasured"}
        try:
            jobs = _connection(read(prefix + f"/actions/runs/{run['id']}/jobs?filter=latest&per_page=100"), "jobs")
            executed = 0
            active = 0
            for job in jobs:
                if (job.get("head_sha") != sha or not isinstance(job.get("steps"), list)
                        or any(not isinstance(step, dict)
                               or step.get("status") not in {"queued", "in_progress", "completed", "pending", "waiting"}
                               for step in job["steps"])):
                    raise Unmeasured("job generation or steps unavailable")
                active += sum(step.get("status") == "in_progress" for step in job["steps"])
                executed += sum(isinstance(step, dict)
                                and step.get("status") == "completed"
                                and step.get("conclusion") in {"success", "failure", "cancelled", "timed_out"}
                                for step in job["steps"])
            row["executed_steps"] = executed + active
            row["active_steps"] = active
            row["jobs_observed"] = len(jobs)
            row["execution"] = "in_progress" if active else ("executed" if executed else "no_executed_steps")
        except (OSError, ValueError, KeyError, TypeError, Unmeasured):
            pass
        observations.append(row)
    return {"status": "measured" if len(runs) <= 10 and all(row["execution"] != "unmeasured" for row in observations) else "unmeasured",
            "runs_total": len(runs), "runs_observed": observations,
            "runs_unmeasured": max(0, len(runs) - 10) + sum(row["execution"] == "unmeasured" for row in observations),
            "acceptance": "unmeasured",
            "boundary": "Executed steps do not establish the owning verification predicate or required workflow coverage."}


def _security(read: Callable, prefix: str) -> dict[str, Any]:
    result = {}
    for name, endpoint in (("dependabot", "dependabot/alerts"),
                           ("code_scanning", "code-scanning/alerts"),
                           ("secret_scanning", "secret-scanning/alerts")):
        try:
            rows = read(prefix + "/" + endpoint + "?state=open&per_page=100")
            result[name] = summarize_alerts(rows, name)
        except (OSError, ValueError, KeyError, TypeError, Unmeasured):
            result[name] = _unknown()
    return result



def collect_health_batch(repositories, token, *, limit=5, offset=0, read=None):
    """Inspect a bounded subset while retaining the supplied inventory denominator.

    One Reader shares the existing request/time budget across the whole batch.
    The caller's inventory is a scope declaration, not proof of estate coverage.
    """
    if (not isinstance(repositories, list) or not repositories or len(repositories) > 10000
            or any(not isinstance(r, str) or not re.fullmatch(
                r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", r) for r in repositories)
            or len({r.lower() for r in repositories}) != len(repositories)):
        raise ValueError("inventory must contain unique OWNER/NAME entries")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("inspection limit must be an integer from 1 to 20")
    if type(offset) is not int or not 0 <= offset < len(repositories):
        raise ValueError("inspection offset must identify an inventory entry")
    shared = read or Reader(token)
    observations = [collect_health(repo, token, read=shared)
                    for repo in repositories[offset:offset + limit]]
    public_ids = [r["repository_id"] for r in observations if "repository_id" in r]
    private = sum(r["scope"]["private_repositories_excluded"] for r in observations)
    unknown = sum(r["scope"]["repositories_unmeasured"] for r in observations)
    return {
        "schema_version": "laurea.health-batch.v1", "status": "unmeasured",
        "scope": {
            "inventory_entries": len(repositories), "entries_attempted": len(observations),
            "selection_offset": offset, "selection_end_exclusive": offset + len(observations),
            "entries_not_attempted": len(repositories) - len(observations),
            "private_entries_excluded": private, "attempted_entries_unmeasured": unknown,
            "public_repository_identities_observed": len(set(public_ids)),
            "duplicate_identity_observations": len(public_ids) - len(set(public_ids)),
            "inventory_completeness": "unmeasured", "health_acceptance": "unmeasured",
        },
        "observations": observations,
    }


def collect_health(repository: str, token: str, *, read: Callable | None = None) -> dict[str, Any]:  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be OWNER/NAME")
    read = read or Reader(token)
    result = {"schema_version": "laurea.health.v1", "status": "unmeasured", "observed_at": datetime.now(timezone.utc).isoformat(),
              "generation": "unmeasured", "verification": _unknown(),
              "security": _unknown(), "pr_readiness": _unknown(),
              "scope": {"repositories_requested": 1, "public_repositories_observed": 0,
                        "private_repositories_excluded": 0, "repositories_unmeasured": 1,
                        "archive_status": "unmeasured",
                        "boundary": "One requested repository; not an administered-estate inventory or health percentage."}}
    prefix = "/repos/" + repository
    redacted = deepcopy(result)
    public_readback = False
    after = None
    try:
        repo = read(prefix)
        if not isinstance(repo, dict) or repo.get("private") is not False:
            result["excluded_private_or_unknown"] = True
            if isinstance(repo, dict) and repo.get("private") is True:
                result["scope"].update(private_repositories_excluded=1, repositories_unmeasured=0)
            return result
        branch = repo["default_branch"]
        if (type(repo.get("id")) is not int or not isinstance(branch, str)
                or not isinstance(repo.get("full_name"), str)):
            raise Unmeasured("repository identity unavailable")
        result["scope"].update(public_repositories_observed=1, repositories_unmeasured=0,
                               archive_status=("archived" if repo["archived"] else "active")
                               if type(repo.get("archived")) is bool else "unmeasured")
        ref = read(prefix + "/commits/" + quote(branch, safe=""))
        sha = ref["sha"]
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise Unmeasured("default SHA unavailable")
        result.update(repository=repo["full_name"], repository_id=repo["id"], default_sha=sha)
        for key, probe in (("verification", lambda: _verification(read, prefix, sha)),
                           ("security", lambda: _security(read, prefix)),
                           ("pr_readiness", lambda: collect_pulls(read, prefix, repo["id"]))):
            try:
                result[key] = probe()
            except (OSError, ValueError, KeyError, TypeError, Unmeasured):
                result[key] = _unknown()
        current = read(prefix + "/commits/" + quote(branch, safe=""))
        after = read(prefix)
        public_readback = (isinstance(after, dict) and after.get("private") is False
                           and type(after.get("id")) is int and after["id"] == repo["id"])
        result["generation"] = "current" if (after.get("id") == repo["id"]
            and after.get("default_branch") == branch and after.get("private") is False
            and after.get("full_name") == repo["full_name"]
            and current.get("sha") == sha) else "not_current"
    except (OSError, ValueError, KeyError, TypeError, AttributeError, Unmeasured):
        pass
    if not public_readback:
        redacted["excluded_private_or_unknown"] = True
        if isinstance(after, dict) and after.get("private") is True:
            redacted["scope"].update(private_repositories_excluded=1, repositories_unmeasured=0)
        return redacted
    result["scope"]["archive_status"] = (
        ("archived" if after["archived"] else "active")
        if type(after.get("archived")) is bool else "unmeasured"
    )
    return result
