"""Bounded exact-head pull observations; no merge or acceptance authority."""
from __future__ import annotations

import re
from typing import Any, Callable


class InvalidPull(ValueError):
    pass


def _generation(value: Any, number: int, repository_id: int) -> tuple:
    if not isinstance(value, dict) or value.get("number") != number:
        raise InvalidPull("pull identity unavailable")
    head, base = value.get("head"), value.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise InvalidPull("pull generation unavailable")
    if (not isinstance(base.get("repo"), dict)
            or type(base["repo"].get("id")) is not int
            or base["repo"].get("id") != repository_id
            or not isinstance(base.get("ref"), str)):
        raise InvalidPull("base repository unavailable")
    for sha in (head.get("sha"), base.get("sha")):
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise InvalidPull("pull SHA unavailable")
    if type(value.get("draft")) is not bool or value.get("state") not in {"open", "closed"}:
        raise InvalidPull("pull state unavailable")
    return head["sha"], base["sha"], base["ref"], value["state"], value["draft"]


def _checks(read: Callable, prefix: str, sha: str) -> dict:
    value = read(prefix + f"/commits/{sha}/check-runs?filter=latest&per_page=100")
    rows = value.get("check_runs") if isinstance(value, dict) else None
    count = value.get("total_count") if isinstance(value, dict) else None
    if (not isinstance(rows, list) or type(count) is not int or count != len(rows)
            or any(not isinstance(row, dict) or row.get("head_sha") != sha for row in rows)):
        raise InvalidPull("check coverage unavailable")
    counts = {"successful": 0, "failing": 0, "pending": 0, "other": 0}
    for row in rows:
        if row.get("status") in {"queued", "in_progress", "waiting", "pending", "requested"}:
            counts["pending"] += 1
        elif row.get("status") == "completed" and row.get("conclusion") == "success":
            counts["successful"] += 1
        elif row.get("status") == "completed" and row.get("conclusion") in {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}:
            counts["failing"] += 1
        else:
            counts["other"] += 1
    return {"status": "measured", "observed": count, **counts,
            "required_policy": "unmeasured",
            "boundary": "Check results alone do not prove trusted producers, executed jobs, or required-check satisfaction."}


def _reviews(read: Callable, prefix: str, number: int, sha: str) -> dict:
    rows = read(prefix + f"/pulls/{number}/reviews?per_page=100")
    if not isinstance(rows, list) or len(rows) >= 100:
        raise InvalidPull("review coverage unavailable")
    latest = {}
    other_heads = 0
    for row in rows:
        if not isinstance(row, dict) or type(row.get("id")) is not int:
            raise InvalidPull("review identity unavailable")
        if row.get("commit_id") != sha:
            other_heads += 1
            continue
        user = row.get("user")
        if not isinstance(user, dict) or type(user.get("id")) is not int:
            raise InvalidPull("reviewer identity unavailable")
        if row.get("state") not in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED", "COMMENTED", "PENDING"}:
            raise InvalidPull("review state unavailable")
        # Comments and drafts do not supersede the same reviewer's decision.
        if row["state"] in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            # GitHub returns reviews in chronological order; numeric IDs are not a clock.
            latest[user["id"]] = row
    return {"status": "measured", "observed": len(rows), "other_head_reviews": other_heads,
            "current_head_approvals": sum(row["state"] == "APPROVED" for row in latest.values()),
            "current_head_changes_requested": sum(row["state"] == "CHANGES_REQUESTED" for row in latest.values()),
            "required_policy": "unmeasured"}


def collect_pulls(read: Callable, prefix: str, repository_id: int) -> dict:
    rows = read(prefix + "/pulls?state=open&per_page=100")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise InvalidPull("malformed pull requests")
    observations = []
    for listed in rows[:5]:
        number = listed.get("number")
        observation = {"status": "unmeasured", "readiness": "unmeasured"}
        observations.append(observation)
        if type(number) is not int or number <= 0:
            continue
        observation["number"] = number
        path = prefix + f"/pulls/{number}"
        try:
            before = read(path)
            generation = _generation(before, number, repository_id)
            sha, base_sha, base_ref, state, draft = generation
            observation.update(head_sha=sha, base_sha=base_sha, base_ref=base_ref,
                               generation="unmeasured", draft=draft,
                               mergeable=before.get("mergeable") if type(before.get("mergeable")) is bool else None,
                               checks={"status": "unmeasured"}, reviews={"status": "unmeasured"})
            for name, probe in (("checks", lambda: _checks(read, prefix, sha)),
                                ("reviews", lambda: _reviews(read, prefix, number, sha))):
                try:
                    observation[name] = probe()
                except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                    pass
            after = read(path)
            current = generation == _generation(after, number, repository_id)
            observation["generation"] = "current" if current else "not_current"
            if current and state == "open":
                observation["status"] = "measured"
                blockers = []
                if draft:
                    blockers.append("draft")
                if before.get("mergeable") is False and after.get("mergeable") is False:
                    blockers.append("merge_conflict")
                observation["blockers"] = blockers
                observation["readiness"] = "blocked" if blockers else "unmeasured"
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            pass
    complete = sum(row.get("generation") == "current"
                   and row.get("status") == "measured"
                   and row.get("checks", {}).get("status") == "measured"
                   and row.get("reviews", {}).get("status") == "measured"
                   for row in observations)
    return {"status": "measured" if len(rows) < 100 and complete == len(rows) else "unmeasured",
            "listing_complete": len(rows) < 100,
            "open_observed": len(rows), "pulls_observed": observations,
            "pulls_unmeasured": len(rows) - complete, "readiness": "unmeasured",
            "boundary": "At most five PRs are inspected. Exact-head observations do not establish required policy, trusted checks, code-owner approval, or the owning acceptance predicate."}
