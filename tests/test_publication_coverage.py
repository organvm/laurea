import pytest

from laurea import cli
from laurea.arena import build_row
from laurea.corpus import aggregate_repositories
from laurea.detectors import run_all
from laurea.models import Report
from laurea.render import hero_card, profile_md, render_all
from laurea.verdict import collect_verdict


def snapshot():
    return {"login": "test", "created_at": "2020-01-01T00:00:00Z", "followers": 1,
            "orgs": [], "repos": [],
            "contributions": dict.fromkeys(["total", "commits", "pull_requests", "reviews", "issues", "restricted"], 0),
            "coverage": {"status": "complete", "organization_scope_complete": True,
                         "failed_sources": 0, "private_repositories_excluded": 0}}


def report(value):
    return Report(login="test", generated_at="2026-09-16T00:00:00Z", snapshot=value,
                  findings=run_all(value))


@pytest.mark.parametrize("coverage", [None, "invalid", {"status": "unmeasured"},
    {"status": "complete", "organization_scope_complete": False, "failed_sources": 0}])
def test_incomplete_compute_preserves_metrics_and_same_day_history(monkeypatch, tmp_path, coverage):
    value = snapshot()
    value["coverage"] = coverage
    metrics = tmp_path / "metrics.json"
    history = tmp_path / "verdict.jsonl"
    metrics.write_text("previous complete metrics")
    history.write_text("previous valid same-day history")
    monkeypatch.setattr(cli, "resolve_token", lambda: "fixture")
    monkeypatch.setattr(cli, "collect", lambda *args: value)
    monkeypatch.setattr(cli, "collect_verdict", lambda *args: pytest.fail("must not collect verdict"))
    with pytest.raises(ValueError, match="coverage"):
        cli._compute("test", tmp_path)
    assert metrics.read_text() == "previous complete metrics"
    assert history.read_text() == "previous valid same-day history"


def test_incomplete_render_and_arena_cannot_publish_partial_counts():
    value = snapshot()
    complete = report(value)
    value["coverage"]["status"] = "unmeasured"
    with pytest.raises(ValueError, match="coverage"):
        render_all(complete)
    with pytest.raises(ValueError, match="coverage"):
        build_row(complete)


def test_private_aggregate_semantics_reach_all_consumers(monkeypatch):
    value = snapshot()
    public = {"isFork": False, "stargazerCount": 2, "primaryLanguage": {"name": "Python"}}
    private = {"isFork": False, "stargazerCount": 5, "primaryLanguage": {"name": "Rust"}}
    private_fork = {"isFork": True, "stargazerCount": 3, "primaryLanguage": {"name": "Go"}}
    value["repos"] = [public]
    value["coverage"]["private_repositories_excluded"] = 2
    value["repository_aggregates"] = aggregate_repositories([public, private, private_fork])
    measured = report(value)
    assert measured.by_axis("repos_visible").value == 2
    assert measured.by_axis("language_breadth").value == 2
    assert build_row(measured)["repos"] == 2
    assert '>2</text>' in hero_card(measured)
    monkeypatch.setattr("laurea.verdict._rest", lambda *args: {})
    assert collect_verdict(value, "owner/repo", "fixture", "2026-09-16")["stars_estate"] == 10
    assert "Go" not in value["repository_aggregates"]["primary_languages"]


def test_redacted_snapshot_without_aggregates_cannot_change_metric_meaning():
    value = snapshot()
    value["coverage"]["private_repositories_excluded"] = 1
    with pytest.raises(ValueError, match="aggregate"):
        run_all(value)


@pytest.mark.parametrize("coverage", [None, "invalid", 1])
def test_direct_profile_handles_malformed_coverage_as_unknown(coverage):
    value = snapshot()
    measured = report(value)
    value["coverage"] = coverage
    assert "Collection: **unmeasured**" in profile_md(measured)
