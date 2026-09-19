"""Actual isolated Git pushes prove the default ref and caller files stay intact."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from laurea import publish as p


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    root, remote = tmp_path / "work", tmp_path / "remote.git"
    root.mkdir()
    def git(*args, cwd=root):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              timeout=10, check=True).stdout.strip()
    git("init", "--bare", str(remote))
    git("init", "-b", "main")
    git("config", "user.name", "fixture")
    git("config", "user.email", "fixture@example.invalid")
    (root / "assets").mkdir()
    (root / "assets/metrics.json").write_text('{"old":true}\n')
    (root / "LEADERBOARD.md").write_text("old table\n")
    (root / "arena/entries").mkdir(parents=True)
    (root / "arena/baseline.json").write_bytes((Path(__file__).resolve().parents[1] / "arena/baseline.json").read_bytes())
    git("add", ".")
    git("commit", "-m", "fixture")
    sha = git("rev-parse", "HEAD")
    git("remote", "add", "origin", str(remote))
    git("push", "origin", "HEAD:refs/heads/main")
    env = {**os.environ, "GITHUB_ACTIONS": "true", "GITHUB_WORKSPACE": str(root),
           "GITHUB_REPOSITORY": "owner/repo", "GITHUB_SHA": sha,
           "GITHUB_RUN_ID": "12", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_EVENT_NAME": "schedule"}
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"action": "opened", "issue": {"number": 4},
                                 "repository": {"full_name": "owner/repo", "id": 7}}))
    env["GITHUB_EVENT_PATH"] = str(event)
    calls, bodies = [], []
    settings = {"create_fails": False, "created": False, "wrong_pr": False, "wrong_origin": False}
    real = p.command
    def command(argv, *, root, env):
        calls.append(argv)
        if argv == ["git", "remote", "get-url", "origin"]:
            return "https://github.com/other/repo" if settings["wrong_origin"] else "https://github.com/owner/repo"
        if argv[0] != "gh":
            return real(argv, root=root, env=env)
        if argv[1:3] == ["pr", "create"]:
            bodies.append(Path(argv[argv.index("--body-file") + 1]).read_text())
            if settings["create_fails"]:
                raise RuntimeError("ambiguous create")
            settings["created"] = True
            return "https://github.com/owner/repo/pull/9"
        assert argv[1] == "api"
        path = argv[2]
        if path == "repos/owner/repo":
            return json.dumps({"id": 7, "full_name": "owner/repo", "default_branch": "main"})
        if "/commits/" in path:
            return json.dumps({"sha": settings.get("default_sha", sha)})
        if "/compare/" in path:
            return json.dumps({"status": "identical"})
        if "/issues/" in path:
            return json.dumps({"number": 4, "state": "open"})
        if "/pulls?state=open&base=" in path:
            return json.dumps(settings.get("pending", []))
        if "/pulls?" in path:
            branch = git("branch", "--show-current")
            return json.dumps([{"state": "open", "number": 9,
                                "head": {"sha": "b" * 40 if settings["wrong_pr"] else git("rev-parse", "HEAD"),
                                         "ref": branch, "repo": {"id": 7}},
                                "base": {"ref": "main", "repo": {"id": 7}}}]
                              if settings["created"] else [])
        raise AssertionError(path)
    monkeypatch.setattr(p, "command", command)
    return root, remote, env, calls, bodies, settings, git, sha


def test_metrics_pushes_only_unique_branch_and_reads_back_pr(sandbox):
    root, remote, env, calls, bodies, _, git, sha = sandbox
    (root / "assets/metrics.json").write_text('{"new":true}\n')
    result = p.publish("metrics", root=root, env=env)
    assert result["status"] == "pr_open"
    assert git("rev-parse", "refs/heads/main", cwd=remote) == sha
    assert git("rev-parse", "refs/heads/automation/metrics/12-1", cwd=remote) == result["head_sha"]
    assert git("diff", "--name-only", sha, result["head_sha"]) == "assets/metrics.json"
    assert "open PR is preparation" in bodies[0]
    assert all("--force" not in call and "--rebase" not in call for call in calls)


def test_arena_record_pr_preserves_issue_until_table_acceptance(sandbox):
    root, _, env, calls, bodies, _, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "issues"
    from laurea.arena import write_entry
    write_entry(root / "arena/entries", issue=4,
                row=dict(login="alice", contributions=1, prs=1, repos=1, languages=1, measured_axes=1, verified="2026-09-16"),
                observed_at="2026-09-16T00:00:00+00:00")
    assert p.publish("arena", issue=4, root=root, env=env)["status"] == "pr_open"
    assert "Records evidence for #4" in bodies[0]
    assert "Closes #" not in bodies[0]
    assert not any(call[0:3] == ["gh", "issue", "close"] for call in calls)


def test_unchanged_artifact_does_not_push_or_close_issue(sandbox):
    root, _, env, calls, _, _, _, _ = sandbox
    assert p.publish("metrics", root=root, env=env)["status"] == "unchanged"
    assert not any(call[:2] == ["git", "push"] or call[:3] == ["gh", "pr", "create"] for call in calls)


def test_arena_cannot_close_an_issue_other_than_its_source(sandbox):
    root, _, env, calls, _, _, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "issues"
    with pytest.raises(ValueError, match="source event"):
        p.publish("arena", issue=5, root=root, env=env)
    assert not any(call[:2] == ["git", "push"] for call in calls)


def test_unrelated_caller_file_is_preserved(sandbox):
    root, _, env, _, _, _, _, _ = sandbox
    (root / "caller.txt").write_text("preserve me")
    with pytest.raises(ValueError, match="unrelated"):
        p.publish("metrics", root=root, env=env)
    assert (root / "caller.txt").read_text() == "preserve me"


def test_existing_branch_is_not_updated(sandbox):
    root, remote, env, _, _, _, git, sha = sandbox
    git("push", "origin", "HEAD:refs/heads/automation/metrics/12-1")
    (root / "assets/metrics.json").write_text("changed")
    with pytest.raises(ValueError, match="already exists"):
        p.publish("metrics", root=root, env=env)
    assert git("rev-parse", "refs/heads/automation/metrics/12-1", cwd=remote) == sha


@pytest.mark.parametrize("created", [True, False])
def test_ambiguous_create_is_read_once_without_retry(sandbox, created):
    root, remote, env, calls, _, settings, git, sha = sandbox
    settings.update(create_fails=True, created=created)
    (root / "assets/metrics.json").write_text("changed")
    receipt = {}
    if created:
        assert p.publish("metrics", root=root, env=env, receipt=receipt)["status"] == "pr_open"
    else:
        with pytest.raises(RuntimeError, match="PR publication"):
            p.publish("metrics", root=root, env=env, receipt=receipt)
        assert receipt["status"] == "branch_published"
    assert git("rev-parse", "refs/heads/main", cwd=remote) == sha
    assert sum(call[:3] == ["gh", "pr", "create"] for call in calls) == 1


def test_wrong_pr_head_cannot_be_accepted(sandbox):
    root, _, env, _, _, settings, _, _ = sandbox
    settings["wrong_pr"] = True
    (root / "assets/metrics.json").write_text("changed")
    with pytest.raises(RuntimeError, match="PR identity"):
        p.publish("metrics", root=root, env=env)


@pytest.mark.parametrize("change", ["origin", "sha", "event"])
def test_untrusted_context_stops_before_push(sandbox, change):
    root, _, env, calls, _, settings, _, _ = sandbox
    if change == "origin":
        settings["wrong_origin"] = True
    elif change == "sha":
        env["GITHUB_SHA"] = "b" * 40
    else:
        env["GITHUB_EVENT_NAME"] = "pull_request"
    with pytest.raises(ValueError):
        p.publish("metrics", root=root, env=env)
    assert not any(call[:2] == ["git", "push"] for call in calls)


def test_failure_receipt_preserves_known_remote_branch_and_redacts_error(monkeypatch, capsys):
    def fail(kind, *, issue, receipt, refresh_table, refresh_pending):
        receipt.update(status="branch_published", branch="automation/metrics/12-1", head_sha="a" * 40)
        raise RuntimeError("PRIVATE provider details")
    monkeypatch.setattr(p, "publish", fail)
    assert p.main(["--kind", "metrics"]) == 1
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["status"] == "unverified"
    assert result["last_verified_state"] == "branch_published"
    assert result["branch"] == "automation/metrics/12-1"
    assert "PRIVATE" not in output


@pytest.mark.parametrize("path", ["LEADERBOARD.md", "arena/entries/5.json"])
def test_arena_rejects_other_issue_or_whole_table_changes(sandbox, path):
    root, _, env, calls, _, _, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "issues"
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("unrelated")
    with pytest.raises(ValueError, match="unrelated"):
        p.publish("arena", issue=4, root=root, env=env)
    assert not any(call[:2] == ["git", "push"] for call in calls)


@pytest.mark.parametrize("mutation", ["boolean_schema", "extra_field", "list"])
def test_arena_rejects_noncanonical_record_before_push(sandbox, mutation):
    root, _, env, calls, _, _, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "issues"
    record = {"schema_version": 1, "issue": 4,
              "observed_at": "2026-09-16T00:00:00+00:00",
              "row": dict(login="alice", contributions=1, prs=1, repos=1,
                          languages=1, measured_axes=1, verified="2026-09-16")}
    if mutation == "boolean_schema":
        record["schema_version"] = True
    elif mutation == "extra_field":
        record["unvalidated"] = "data"
    else:
        record = []
    path = root / "arena/entries/4.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="source issue"):
        p.publish("arena", issue=4, root=root, env=env)
    assert path.read_bytes() == before
    assert not any(call[:2] == ["git", "push"] for call in calls)


def test_table_publication_uses_complete_baseline_and_unique_pr(sandbox):
    from laurea.arena import materialize_entries
    root, remote, env, calls, bodies, _, git, sha = sandbox
    env["GITHUB_EVENT_NAME"] = "push"
    materialize_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
    result = p.publish("arena-table", root=root, env=env)
    assert result["status"] == "pr_open"
    assert git("rev-parse", "refs/heads/main", cwd=remote) == sha
    assert git("diff", "--name-only", sha, result["head_sha"]) == "LEADERBOARD.md"
    assert not any("--force" in call for call in calls)
    assert "Closes #" not in bodies[0]


def test_table_publication_rejects_moved_default_before_push(sandbox):
    root, _, env, calls, _, settings, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "push"
    settings["default_sha"] = "b" * 40
    with pytest.raises(ValueError, match="current default generation"):
        p.publish("arena-table", root=root, env=env)
    assert not any(call[:2] == ["git", "push"] for call in calls)


def test_table_publication_rejects_incomplete_render(sandbox):
    root, _, env, calls, _, _, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "push"
    (root / "LEADERBOARD.md").write_text("missing accepted historical row")
    with pytest.raises(ValueError, match="stale"):
        p.publish("arena-table", root=root, env=env)
    assert not any(call[:2] == ["git", "push"] for call in calls)


@pytest.mark.parametrize("count", [1, 2])
def test_pending_table_prs_retain_ownership_without_mutation(sandbox, count):
    from laurea.arena import materialize_entries
    root, _, env, calls, _, settings, git, sha = sandbox
    env["GITHUB_EVENT_NAME"] = "push"
    settings["pending"] = [{"number": n, "state": "open",
        "head": {"ref": f"automation/arena-table/{n}-1", "sha": "a" * 40, "repo": {"id": 7}},
        "base": {"ref": "main", "repo": {"id": 7}}} for n in range(1, count + 1)]
    materialize_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
    result = p.publish("arena-table", root=root, env=env)
    assert result["status"] == "pending_predecessor"
    assert len(result["pending"]) == count
    assert git("rev-parse", "HEAD") == sha
    assert git("diff", "--cached", "--name-only") == ""
    assert not any(call[:2] == ["git", "push"] or call[:3] == ["gh", "pr", "create"] for call in calls)


def test_saturated_table_owner_inventory_fails_closed(sandbox):
    from laurea.arena import materialize_entries
    root, _, env, calls, _, settings, _, _ = sandbox
    env["GITHUB_EVENT_NAME"] = "push"
    settings["pending"] = [{}] * 100
    materialize_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
    with pytest.raises(ValueError, match="inventory incomplete"):
        p.publish("arena-table", root=root, env=env)
    assert not any(call[:2] == ["git", "push"] for call in calls)


def test_independently_merged_entrants_both_reach_table_pr(sandbox):
    from laurea.arena import write_entry, materialize_entries
    root, remote, env, _, _, settings, git, original = sandbox
    for issue, login in [(1, "alice"), (2, "bob")]:
        git("switch", "-c", f"entrant-{issue}", original)
        write_entry(root / "arena/entries", issue=issue,
                    row=dict(login=login, contributions=issue, prs=1, repos=1,
                             languages=1, measured_axes=1, verified="2026-09-16"),
                    observed_at="2026-09-16T00:00:00Z")
        git("add", f"arena/entries/{issue}.json")
        git("commit", "-m", f"accepted {login}")
    git("switch", "main")
    git("merge", "--no-edit", "entrant-1")
    git("merge", "--no-edit", "entrant-2")
    accepted = git("rev-parse", "HEAD")
    git("push", "origin", "main")
    env.update(GITHUB_EVENT_NAME="push", GITHUB_SHA=accepted)
    settings["default_sha"] = accepted
    materialize_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
    result = p.publish("arena-table", root=root, env=env)
    rendered = git("show", result["head_sha"] + ":LEADERBOARD.md", cwd=remote)
    assert all("@" + login in rendered for login in ("alice", "bob", "4444J99"))
    assert git("rev-parse", "main", cwd=remote) == accepted
    assert git("diff", "--name-only", accepted, result["head_sha"]) == "LEADERBOARD.md"


@pytest.mark.parametrize("foreign_change,outcome", [(False, "normal"), (True, "normal"),
    (False, "timeout_after"), (False, "timeout_before"), (False, "concurrent")])
def test_refresh_existing_table_fast_forwards_or_rejects_foreign_work(sandbox, monkeypatch, foreign_change, outcome):
    from laurea.arena import materialize_entries, write_entry
    root, remote, env, calls, _, settings, git, original = sandbox
    branch = "automation/arena-table/9-1"
    git("switch", "-c", branch)
    materialize_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
    git("add", "LEADERBOARD.md")
    if foreign_change:
        (root / "foreign.txt").write_text("preserve")
        git("add", "foreign.txt")
    git("commit", "-m", "previous table proposal")
    previous = git("rev-parse", "HEAD")
    git("push", "origin", branch)
    git("switch", "main")
    write_entry(root / "arena/entries", issue=1,
                row=dict(login="alice", contributions=1, prs=1, repos=1, languages=1,
                         measured_axes=1, verified="2026-09-16"), observed_at="2026-09-16T00:00:00Z")
    git("add", "arena/entries/1.json")
    git("commit", "-m", "accepted entrant")
    accepted = git("rev-parse", "HEAD")
    git("push", "origin", "main")
    env.update(GITHUB_EVENT_NAME="push", GITHUB_SHA=accepted)
    settings["default_sha"] = accepted
    settings["pending"] = [{"number": 9, "state": "open",
        "head": {"ref": branch, "sha": previous, "repo": {"id": 7}},
        "base": {"ref": "main", "repo": {"id": 7}}}]
    materialize_entries(root / "arena/entries", root / "LEADERBOARD.md", baseline=root / "arena/baseline.json")
    if foreign_change:
        with pytest.raises(ValueError, match="outside generated scope"):
            p.publish("arena-table", root=root, env=env, refresh_table=True)
        assert git("rev-parse", branch, cwd=remote) == previous
        return
    underlying = p.command
    attempts = []
    rival = None
    if outcome == "concurrent":
        # Independent fast-forward update of the same predecessor.
        tree = git("rev-parse", previous + "^{tree}")
        rival = git("commit-tree", tree, "-p", previous, "-m", "concurrent owner update")
    def racing_command(argv, *, root, env):
        if argv[:3] == ["git", "push", "origin"]:
            attempts.append(argv)
            if outcome == "timeout_before":
                raise subprocess.TimeoutExpired(argv, 30)
            if outcome == "concurrent":
                git("push", "origin", rival + ":refs/heads/" + branch)
            result = underlying(argv, root=root, env=env)
            if outcome == "timeout_after":
                raise subprocess.TimeoutExpired(argv, 30)
            return result
        return underlying(argv, root=root, env=env)
    monkeypatch.setattr(p, "command", racing_command)
    receipt = {}
    if outcome in {"timeout_before", "concurrent"}:
        with pytest.raises(RuntimeError, match="refresh unverified"):
            p.publish("arena-table", root=root, env=env, refresh_table=True, receipt=receipt)
        assert len(attempts) == 1
        assert git("rev-parse", branch, cwd=remote) == (rival or previous)
        assert receipt["predecessor_sha"] == previous
        assert receipt["head_sha"] != previous
        assert receipt["pr_url"].endswith("/pull/9")
        assert git("rev-parse", "main", cwd=remote) == accepted
        return
    result = p.publish("arena-table", root=root, env=env, refresh_table=True)
    assert len(attempts) == 1
    assert result["status"] == "table_branch_refreshed"
    new = git("rev-parse", branch, cwd=remote)
    assert git("show", "-s", "--format=%P", new).split() == [previous, accepted]
    assert "@alice" in git("show", new + ":LEADERBOARD.md", cwd=remote)
    assert git("rev-parse", "main", cwd=remote) == accepted
    assert not any(call[:3] == ["gh", "pr", "create"] or "--force" in call for call in calls)


@pytest.mark.parametrize("empty_advance", [False, True])
def test_metrics_refresh_reuses_existing_pr_and_preserves_new_default(sandbox, empty_advance):
    root, remote, env, calls, _, settings, git, original = sandbox
    branch = "automation/metrics/9-1"
    git("switch", "-c", branch)
    (root / "assets/metrics.json").write_text('{"previous":true}')
    git("add", "assets")
    git("commit", "-m", "previous metrics proposal")
    previous = git("rev-parse", "HEAD")
    git("push", "origin", branch)
    git("switch", "main")
    if not empty_advance:
        (root / "accepted.txt").write_text("accepted default change")
        git("add", "accepted.txt")
    git("commit", "--allow-empty", "-m", "advance default")
    accepted = git("rev-parse", "HEAD")
    git("push", "origin", "main")
    env["GITHUB_SHA"] = accepted
    settings["default_sha"] = accepted
    settings["pending"] = [{"number": 9, "state": "open",
        "head": {"ref": branch, "sha": previous, "repo": {"id": 7}},
        "base": {"ref": "main", "repo": {"id": 7}}}]
    content = '{"previous":true}' if empty_advance else '{"current":true}'
    (root / "assets/metrics.json").write_text(content)
    result = p.publish("metrics", root=root, env=env, refresh_pending=True)
    assert result["status"] == "metrics_branch_refreshed"
    new = git("rev-parse", branch, cwd=remote)
    if not empty_advance:
        assert git("show", new + ":accepted.txt", cwd=remote) == "accepted default change"
    assert git("show", new + ":assets/metrics.json", cwd=remote) == content
    assert git("show", "-s", "--format=%P", new).split() == [previous, accepted]
    assert git("rev-parse", "main", cwd=remote) == accepted
    assert not any(call[:3] == ["gh", "pr", "create"] or "--force" in call for call in calls)


@pytest.mark.parametrize("current_date,expected", [
    ("2026-09-19", [("2026-09-18", 1), ("2026-09-19", 2)]),
    ("2026-09-18", [("2026-09-18", 2)]),
])
def test_metrics_refresh_preserves_pending_history_by_date(sandbox, current_date, expected):
    root, remote, env, _, _, settings, git, original = sandbox
    branch = "automation/metrics/9-1"
    git("switch", "-c", branch)
    (root / "assets/verdict.jsonl").write_text(
        json.dumps({"date": "2026-09-18", "followers": 1}) + "\n"
    )
    git("add", "assets")
    git("commit", "-m", "previous metrics proposal")
    previous = git("rev-parse", "HEAD")
    git("push", "origin", branch)
    git("switch", "main")
    git("commit", "--allow-empty", "-m", "advance default")
    accepted = git("rev-parse", "HEAD")
    git("push", "origin", "main")
    env["GITHUB_SHA"] = accepted
    settings["default_sha"] = accepted
    settings["pending"] = [{"number": 9, "state": "open",
        "head": {"ref": branch, "sha": previous, "repo": {"id": 7}},
        "base": {"ref": "main", "repo": {"id": 7}}}]
    (root / "assets/verdict.jsonl").write_text(
        json.dumps({"date": current_date, "followers": 2}) + "\n"
    )

    result = p.publish("metrics", root=root, env=env, refresh_pending=True)

    rows = [json.loads(line) for line in git(
        "show", result["head_sha"] + ":assets/verdict.jsonl", cwd=remote
    ).splitlines()]
    assert [(row["date"], row["followers"]) for row in rows] == expected
    assert git("show", "-s", "--format=%P", result["head_sha"], cwd=remote).split() == [previous, accepted]
