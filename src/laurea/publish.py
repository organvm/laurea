"""Publish generated files through a unique PR branch, never the default ref."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote


def command(argv, *, root, env):
    result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=30)
    if result.returncode or len(result.stdout) + len(result.stderr) > 2_000_000:
        raise RuntimeError("publication command did not complete")
    return result.stdout.rstrip("\n")


def publish(kind, *, issue=None, root=None, env=None, receipt=None, refresh_table=False, refresh_pending=False):
    root = Path(root or Path.cwd()).resolve()
    env = dict(os.environ if env is None else env)
    receipt = {} if receipt is None else receipt
    repository = env.get("GITHUB_REPOSITORY", "")
    sha = env.get("GITHUB_SHA", "")
    run_id, attempt = env.get("GITHUB_RUN_ID", ""), env.get("GITHUB_RUN_ATTEMPT", "")
    allowed_events = {"metrics": {"schedule", "workflow_dispatch", "push"}, "arena": {"issues"}, "arena-table": {"push", "workflow_dispatch"}}
    if (env.get("GITHUB_ACTIONS") != "true" or kind not in allowed_events
            or env.get("GITHUB_EVENT_NAME") not in allowed_events[kind]
            or Path(env.get("GITHUB_WORKSPACE", "/")).resolve() != root
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
            or not re.fullmatch(r"[1-9][0-9]*", run_id)
            or not re.fullmatch(r"[1-9][0-9]*", attempt)
            or (kind == "arena" and (type(issue) is not int or issue <= 0))):
        raise ValueError("trusted publication context required")
    branch = f"automation/{kind}/{run_id}-{attempt}"
    receipt.update(schema_version="laurea.publication.v1", repository=repository,
                   source_sha=sha, branch=branch, status="preparing",
                   owner_run=f"https://github.com/{repository}/actions/runs/{run_id}")
    if kind == "arena":
        event_path = Path(env.get("GITHUB_EVENT_PATH", ""))
        if not event_path.is_file() or event_path.stat().st_size > 1_000_000:
            raise ValueError("arena event unavailable")
        event = json.loads(event_path.read_text())
        event_issue = event.get("issue", {})
        if (event.get("action") != "opened" or event_issue.get("number") != issue
                or "pull_request" in event_issue
                or event.get("repository", {}).get("full_name") != repository):
            raise ValueError("arena issue does not match its source event")

    def run(*argv):
        return command(list(argv), root=root, env=env)

    def api(path):
        return json.loads(run("gh", "api", f"repos/{repository}{path}"))

    if run("git", "rev-parse", "HEAD") != sha:
        raise ValueError("checkout identity mismatch")
    origin = run("git", "remote", "get-url", "origin").removesuffix(".git")
    if origin not in {"https://github.com/" + repository, "git@github.com:" + repository}:
        raise ValueError("push destination does not match the repository")
    if run("git", "diff", "--cached", "--name-only"):
        raise ValueError("caller index is not empty")
    repo = api("")
    default = repo.get("default_branch")
    if (repo.get("full_name") != repository or type(repo.get("id")) is not int or repo["id"] <= 0
            or not isinstance(default, str) or not default or default == branch):
        raise ValueError("repository identity unavailable")
    default_sha = api("/commits/" + quote(default, safe=""))["sha"]
    if not isinstance(default_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", default_sha):
        raise ValueError("default generation unavailable")
    if kind in {"arena-table", "metrics"} and default_sha != sha:
        raise ValueError("table source is not the current default generation")
    if kind == "arena":
        current_issue = api(f"/issues/{issue}")
        if (current_issue.get("number") != issue or current_issue.get("state") != "open"
                or "pull_request" in current_issue or event["repository"].get("id") != repo["id"]):
            raise ValueError("arena issue is no longer an open source obligation")
    comparison = api(f"/compare/{sha}...{default_sha}")
    if comparison.get("status") not in {"ahead", "identical"}:
        raise ValueError("source is not on the default branch")
    entry_path = f"arena/entries/{issue}.json"
    paths = ["assets"] if kind == "metrics" else (["LEADERBOARD.md"] if kind == "arena-table" else [entry_path])
    changed = run("git", "diff", "--name-only", "-z").split("\0")
    changed += run("git", "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    if any(p and not (p.startswith("assets/") if kind == "metrics" else p in paths) for p in changed):
        raise ValueError("unrelated caller files are present")
    if kind == "arena":
        entry = root / entry_path
        if any(parent.is_symlink() for parent in (root / "arena", root / "arena/entries", entry)):
            raise ValueError("arena record symlinks cannot be published")
        if not entry.is_file() or entry.stat().st_size > 10000:
            raise ValueError("bounded arena record required")
        record = json.loads(entry.read_text())
        if (not isinstance(record, dict)
                or set(record) != {"schema_version", "issue", "observed_at", "row"}
                or type(record["schema_version"]) is not int or record["schema_version"] != 1
                or type(record["issue"]) is not int or record["issue"] != issue):
            raise ValueError("arena record does not match source issue")
        # Reuse the writer's validation without changing the caller record.
        from .arena import write_entry
        with tempfile.TemporaryDirectory() as validation:
            write_entry(Path(validation), issue=issue, row=record["row"], observed_at=record["observed_at"])
    if kind == "arena-table":
        from .arena import check_materialized_entries
        check_materialized_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
        if api("/commits/" + quote(default, safe=""))["sha"] != sha:
            raise ValueError("default moved during table validation")
    if kind in {"arena-table", "metrics"}:
        pulls = api("/pulls?state=open&base=" + quote(default, safe="") + "&per_page=100")
        if not isinstance(pulls, list) or len(pulls) >= 100:
            raise ValueError("publication ownership inventory incomplete")
        pending = []
        for pr in pulls:
            if not isinstance(pr, dict) or not isinstance(pr.get("head"), dict):
                raise ValueError("malformed open PR inventory")
            head = pr["head"]
            if not isinstance(head.get("ref"), str):
                raise ValueError("open PR branch identity unavailable")
            if not head["ref"].startswith(f"automation/{kind}/"):
                continue
            if (pr.get("state") != "open" or type(pr.get("number")) is not int or pr["number"] <= 0
                    or head.get("repo", {}).get("id") != repo["id"]
                    or pr.get("base", {}).get("repo", {}).get("id") != repo["id"]
                    or pr.get("base", {}).get("ref") != default
                    or not isinstance(head.get("sha"), str) or not re.fullmatch(r"[0-9a-f]{40}", head["sha"])):
                raise ValueError("pending publication PR identity unavailable")
            pending.append({"pr_url": f"https://github.com/{repository}/pull/{pr['number']}",
                            "head_sha": head["sha"], "branch": head["ref"]})
        if len(pending) == 1 and (refresh_pending or (kind == "arena-table" and refresh_table)):
            owner = pending[0]
            receipt.update(status="pending_predecessor", pending=pending, branch=owner["branch"], pr_url=owner["pr_url"])
            head = refresh_pending_branch(run, owner, sha, receipt, kind=kind, root=root)
            receipt.update(status="table_branch_refreshed" if kind == "arena-table" else "metrics_branch_refreshed", pending=pending, head_sha=head,
                           pr_url=owner["pr_url"], branch=owner["branch"],
                           boundary="Existing proposal advanced without force; merge and current-tree verification remain required.")
            return receipt
        if pending:
            receipt.update(status="pending_predecessor", pending=pending,
                           boundary="Existing proposals retain ownership; no new branch or PR was created.",
                           next_action="Reconcile the named PR through the merge rail; rerun from the current default after disposition.")
            return receipt
    run("git", "add", "--", *paths)
    staged = run("git", "diff", "--cached", "--name-only", "-z")
    if not staged:
        receipt.update(status="unchanged", boundary="No generated diff; no new publication or issue closure.")
        return receipt
    modes = run("git", "ls-files", "--stage", "-z", "--", *paths).split("\0")
    if any(row.startswith("120000 ") for row in modes):
        raise ValueError("generated symlinks cannot be published")
    if run("git", "ls-remote", "origin", "refs/heads/" + branch):
        raise ValueError("publication branch already exists; reconcile its owner run")
    run("git", "switch", "-c", branch)
    run("git", "-c", "user.name=laurea[bot]", "-c", "user.email=actions@github.com",
        "commit", "-m", f"{kind}: generated snapshot from {sha[:12]}")
    head = run("git", "rev-parse", "HEAD")
    receipt["head_sha"] = head
    # No force, rebase, default-ref push, retry, or automatic merge.
    push_failed = False
    try:
        run("git", "push", "origin", f"HEAD:refs/heads/{branch}")
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        push_failed = True
    remote = run("git", "ls-remote", "origin", "refs/heads/" + branch)
    if remote.split() != [head, "refs/heads/" + branch]:
        raise RuntimeError("branch publication is unverified")
    receipt.update(status="branch_published", push_reconciled=push_failed)
    body = (f"Generated {kind} snapshot from default-source commit {sha}.\n\n"
            f"Owner and generation receipt: {receipt['owner_run']}\n\n"
            "Review the generated diff and merge through the repository rail. "
            "An open PR is preparation, not publication.\n")
    if kind == "arena":
        body += f"\nRecords evidence for #{issue}. Keep the issue open until its row is materialized and accepted on the default branch.\n"
    fd, body_path = tempfile.mkstemp(prefix="laurea-publication-", suffix=".md")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(body)
        try:
            run("gh", "pr", "create", "--repo", repository, "--base", default,
                "--head", branch, "--title", f"{kind}: refresh generated snapshot",
                "--body-file", body_path)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass  # One readback reconciles an ambiguous create; never send it again.
        pulls = api("/pulls?state=open&head=" + quote(repository.split("/")[0] + ":" + branch, safe="")
                    + "&base=" + quote(default, safe="") + "&per_page=100")
        if not isinstance(pulls, list) or len(pulls) != 1:
            raise RuntimeError("PR publication is unverified; preserve the remote branch")
        pr = pulls[0]
        if (pr.get("head", {}).get("sha") != head
                or pr.get("state") != "open" or pr.get("head", {}).get("ref") != branch
                or pr.get("head", {}).get("repo", {}).get("id") != repo["id"]
                or pr.get("base", {}).get("repo", {}).get("id") != repo["id"]
                or pr.get("base", {}).get("ref") != default
                or type(pr.get("number")) is not int or pr["number"] <= 0):
            raise RuntimeError("PR identity is unverified")
        receipt.update(status="pr_open", pr_url=f"https://github.com/{repository}/pull/{pr['number']}")
        return receipt
    finally:
        Path(body_path).unlink(missing_ok=True)



def refresh_pending_branch(run, owner, source_sha, receipt, *, kind="arena-table", root=None):
    """Advance an owned generated proposal from the validated source checkout."""
    branch, old = owner["branch"], owner["head_sha"]
    if not re.fullmatch(r"automation/" + re.escape(kind) + r"/[1-9][0-9]*-[1-9][0-9]*", branch):
        raise ValueError("unrecognized table branch")
    if run("git", "ls-remote", "origin", "refs/heads/" + branch).split() != [old, "refs/heads/" + branch]:
        raise ValueError("table predecessor moved")
    run("git", "fetch", "--no-tags", "origin", old)
    base = run("git", "merge-base", source_sha, old)
    changes = run("git", "diff", "--name-only", base, old).splitlines()
    if (not changes or any(not (path.startswith("assets/") if kind == "metrics" else path == "LEADERBOARD.md") for path in changes)):
        raise ValueError("predecessor contains changes outside generated scope")
    if kind == "metrics":
        merge_pending_metrics_history(run, root=Path(root or Path.cwd()), predecessor=old)
    scope = "assets" if kind == "metrics" else "LEADERBOARD.md"
    run("git", "add", "--", scope)
    modes = run("git", "ls-files", "--stage", "-z", "--", scope).split("\0")
    if any(row.startswith("120000 ") for row in modes):
        raise ValueError("generated symlinks cannot be published")
    tree = run("git", "write-tree")
    if run("git", "rev-parse", old + "^{tree}") == tree and base == source_sha:
        return old
    # Two parents preserve the predecessor and bind all accepted default changes.
    head = run("git", "-c", "user.name=laurea[bot]", "-c", "user.email=actions@github.com",
               "commit-tree", tree, "-p", old, "-p", source_sha,
               "-m", kind + ": refresh from " + source_sha)
    receipt.update(status="table_refresh_prepared", head_sha=head, predecessor_sha=old)
    try:
        run("git", "push", "origin", head + ":refs/heads/" + branch)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        pass  # Read back once; never retry an ambiguous push.
    if run("git", "ls-remote", "origin", "refs/heads/" + branch).split() != [head, "refs/heads/" + branch]:
        raise RuntimeError("table refresh unverified; reconcile existing proposal")
    return head


def merge_pending_metrics_history(run, *, root, predecessor):
    """Retain unmerged daily verdict observations when refreshing a metrics PR."""
    relative = "assets/verdict.jsonl"
    history = root / relative
    if history.is_symlink():
        raise ValueError("metrics history symlinks cannot be published")
    if run("git", "ls-tree", "--name-only", predecessor, "--", relative) != relative:
        return

    def parse(value, source):
        rows, dates = [], set()
        for line in value.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            date = row.get("date") if isinstance(row, dict) else None
            if not isinstance(date, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date) or date in dates:
                raise ValueError(f"{source} metrics history is malformed")
            dates.add(date)
            rows.append(row)
        return rows

    previous = parse(run("git", "show", predecessor + ":" + relative), "pending")
    current = parse(history.read_text() if history.is_file() else "", "current")
    # Current generation wins for a same-day rerun; distinct predecessor dates
    # remain part of the refreshed proposal even before the predecessor merges.
    merged = {row["date"]: row for row in previous}
    merged.update({row["date"]: row for row in current})
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text("".join(json.dumps(merged[date]) + "\n" for date in sorted(merged)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=("metrics", "arena", "arena-table"))
    parser.add_argument("--issue", type=int)
    parser.add_argument("--refresh-table", action="store_true")
    parser.add_argument("--refresh-pending", action="store_true")
    args = parser.parse_args(argv)
    receipt = {}
    try:
        publish(args.kind, issue=args.issue, receipt=receipt, refresh_table=args.refresh_table, refresh_pending=args.refresh_pending)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError, subprocess.TimeoutExpired):
        receipt.update(last_verified_state=receipt.get("status", "none"), status="unverified",
                       reason="publication requires reconciliation; no retry was attempted")
        print(json.dumps(receipt, indent=2))
        return 1
    print(json.dumps(receipt, indent=2))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a") as stream:
            stream.write(f"status={receipt['status']}\npr_url={receipt.get('pr_url', '')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
