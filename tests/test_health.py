"""Health observations preserve generation and missing-evidence boundaries."""
import json
import pytest
from laurea.health import collect_health, Reader, Unmeasured

SHA = "a" * 40


def reader(*, steps=None, private=False, moved=False, denied=False):
    calls = []
    def read(path):
        calls.append(path)
        if path == "/repos/owner/repo":
            return {"id": 7, "full_name": "owner/repo", "private": private, "default_branch": "main"}
        if "/commits/" in path:
            return {"sha": "b" * 40 if moved and calls.count(path) > 1 else SHA}
        if "/actions/runs?" in path:
            return {"total_count": 1, "workflow_runs": [{"id": 1, "head_sha": SHA, "conclusion": "failure"}]}
        if "/jobs?" in path:
            return {"total_count": 1, "jobs": [{"head_sha": SHA, "steps": steps or []}]}
        if "/alerts?" in path:
            if denied:
                raise OSError("secret provider details")
            return []
        if "/pulls?" in path:
            return []
        raise AssertionError(path)
    return read, calls


def test_zero_step_failure_is_not_executed_code_failure():
    read, _ = reader()
    result = collect_health("owner/repo", "token", read=read)
    assert result["generation"] == "current"
    row = result["verification"]["runs_observed"][0]
    assert row["conclusion"] == "failure"
    assert row["execution"] == "no_executed_steps"
    assert result["verification"]["acceptance"] == "unmeasured"


def test_executed_steps_preserve_separate_acceptance():
    read, _ = reader(steps=[{"status": "completed", "conclusion": "failure"}])
    result = collect_health("owner/repo", "token", read=read)
    assert result["verification"]["runs_observed"][0]["execution"] == "executed"
    assert result["pr_readiness"]["readiness"] == "unmeasured"


def test_head_movement_invalidates_generation():
    read, _ = reader(moved=True)
    assert collect_health("owner/repo", "token", read=read)["generation"] == "not_current"


def test_denied_security_does_not_report_zero_alerts():
    read, _ = reader(denied=True)
    result = collect_health("owner/repo", "token", read=read)
    assert all(value == {"status": "unmeasured"} for value in result["security"].values())
    assert "secret provider" not in json.dumps(result)


def test_private_identity_is_excluded_before_other_reads():
    read, calls = reader(private=True)
    result = collect_health("owner/repo", "token", read=read)
    assert "owner/repo" not in json.dumps(result)
    assert len(calls) == 1
    assert result["scope"]["repositories_requested"] == 1
    assert result["scope"]["private_repositories_excluded"] == 1
    assert result["scope"]["repositories_unmeasured"] == 0


def test_unknown_visibility_stays_in_the_unmeasured_denominator():
    read, calls = reader(private=None)
    result = collect_health("owner/repo", "token", read=read)
    assert result["scope"]["repositories_unmeasured"] == 1
    assert result["scope"]["private_repositories_excluded"] == 0
    assert len(calls) == 1


@pytest.mark.parametrize("final", [True, None, "denied", "malformed", "changed_identity"])
def test_failed_public_readback_scrubs_identity_and_all_findings(final):
    base, calls = reader()
    def read(path):
        value = base(path)
        if path == "/repos/owner/repo" and calls.count(path) == 2:
            if final == "denied":
                raise OSError("PRIVATE_ERROR_DETAIL")
            if final == "malformed":
                return []
            if final == "changed_identity":
                return {**value, "id": 8}
            value["private"] = final
        return value
    result = collect_health("owner/repo", "fixture", read=read)
    rendered = json.dumps(result)
    assert "owner/repo" not in rendered
    assert SHA not in rendered
    assert "repository_id" not in result
    assert "PRIVATE_ERROR_DETAIL" not in rendered
    assert result["verification"] == {"status": "unmeasured"}
    assert result["security"] == {"status": "unmeasured"}
    assert result["pr_readiness"] == {"status": "unmeasured"}
    assert result["scope"]["public_repositories_observed"] == 0
    assert result["scope"]["private_repositories_excluded"] == (1 if final is True else 0)


def test_archived_public_repository_remains_included():
    base, _ = reader()
    def read(path):
        value = base(path)
        if path == "/repos/owner/repo":
            value["archived"] = True
        return value
    result = collect_health("owner/repo", "token", read=read)
    assert result["scope"]["archive_status"] == "archived"
    assert result["scope"]["public_repositories_observed"] == 1
    assert result["scope"]["repositories_unmeasured"] == 0
    assert result["status"] == "unmeasured"


@pytest.mark.parametrize("initial,final,expected", [
    (False, True, "archived"),
    (True, False, "active"),
    (False, None, "unmeasured"),
    (True, "false", "unmeasured"),
])
def test_archive_status_uses_final_public_readback(initial, final, expected):
    base, calls = reader()
    def read(path):
        value = base(path)
        if path == "/repos/owner/repo":
            value["archived"] = initial if calls.count(path) == 1 else final
        return value
    result = collect_health("owner/repo", "fixture", read=read)
    assert result["scope"]["archive_status"] == expected
    assert result["generation"] == "current"
    assert result["status"] == "unmeasured"


def test_security_counts_flow_into_health_without_alert_details():
    base, _ = reader()
    def read(path):
        if "/dependabot/alerts?" in path:
            return [{"number": 1, "state": "open", "html_url": "PRIVATE",
                     "security_vulnerability": {"severity": "critical"}}]
        return base(path)
    result = collect_health("owner/repo", "token", read=read)
    assert result["security"]["dependabot"]["severity_counts_observed"]["critical"] == 1
    assert "PRIVATE" not in json.dumps(result)
    assert result["status"] == "unmeasured"


def test_truncated_runs_remain_unmeasured():
    base, _ = reader()
    def read(path):
        if "/actions/runs?" in path:
            return {"total_count": 101, "workflow_runs": []}
        return base(path)
    assert collect_health("owner/repo", "token", read=read)["verification"] == {"status": "unmeasured"}


def test_wrong_run_generation_cannot_be_used():
    base, _ = reader()
    def read(path):
        if "/actions/runs?" in path:
            return {"total_count": 1, "workflow_runs": [{"id": 1, "head_sha": "b" * 40}]}
        return base(path)
    assert collect_health("owner/repo", "token", read=read)["verification"] == {"status": "unmeasured"}


def test_budget_exhaustion_does_not_issue_network_request():
    with pytest.raises(Unmeasured):
        Reader("token", requests=0)("/repos/owner/repo")


@pytest.mark.parametrize("repo", ["../x/y", "owner/repo?token=secret", "owner"])  # allow-secret: runtime parameter or synthetic rejection fixture; no credential literal
def test_coordinate_rejected_before_network(repo):
    with pytest.raises(ValueError):
        collect_health(repo, "token")


def test_cli_unknown_health_returns_77_even_with_current_generation(monkeypatch, capsys):
    from laurea.cli import main
    monkeypatch.setattr("laurea.cli.resolve_token", lambda: "token")
    monkeypatch.setattr("laurea.cli.collect_health", lambda *args: {
        "status": "unmeasured", "generation": "current"})
    assert main(["health", "--repo", "owner/repo"]) == 77
    assert json.loads(capsys.readouterr().out)["generation"] == "current"


def test_failed_job_observation_keeps_verification_unmeasured():
    base, _ = reader()
    def read(path):
        if "/jobs?" in path:
            raise OSError("unavailable")
        return base(path)
    result = collect_health("owner/repo", "fixture", read=read)
    assert result["verification"]["status"] == "unmeasured"
    assert result["verification"]["runs_observed"][0]["execution"] == "unmeasured"


def test_malformed_steps_do_not_become_measured_zero_execution():
    read, _ = reader(steps=["malformed"])
    result = collect_health("owner/repo", "fixture", read=read)
    assert result["verification"]["status"] == "unmeasured"
    assert result["verification"]["runs_observed"][0]["execution"] == "unmeasured"


def test_active_step_is_positive_execution_evidence():
    read, _ = reader(steps=[{"status": "in_progress", "conclusion": None}])
    result = collect_health("owner/repo", "fixture", read=read)["verification"]
    row = result["runs_observed"][0]
    assert row["execution"] == "in_progress"
    assert row["active_steps"] == 1
    assert row["executed_steps"] == 1
    assert result["acceptance"] == "unmeasured"


def test_unknown_children_and_omitted_runs_share_denominator():
    base, _ = reader()
    def read(path):
        if "/actions/runs?" in path:
            return {"total_count": 12, "workflow_runs": [
                {"id": number, "head_sha": SHA, "conclusion": "failure"}
                for number in range(12)]}
        if "/runs/0/jobs?" in path:
            raise OSError("unavailable")
        return base(path)
    result = collect_health("owner/repo", "fixture", read=read)["verification"]
    assert result["runs_total"] == 12
    assert len(result["runs_observed"]) == 10
    assert result["runs_unmeasured"] == 3
    assert result["status"] == "unmeasured"
