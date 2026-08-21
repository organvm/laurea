"""Tests for bounded snapshot semantics, provenance, and rendering."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pytest

from laurea.baselines import STATUS_DERIVED, STATUS_MEASURED
from laurea.cli import _compute, _load
from laurea.detectors import run_all
from laurea.models import Report
from laurea.render import PUBLIC_LIMITATION, render_all


def _snapshot(**overrides):
    base = {
        "login": "tester",
        "name": "Tester",
        "created_at": "2016-12-27T17:24:06Z",
        "followers": 38,
        "orgs": [f"org{index}" for index in range(10)],
        "repos": (
            [
                {
                    "name": f"py{index}",
                    "isFork": False,
                    "isArchived": False,
                    "stargazerCount": 1,
                    "pushedAt": None,
                    "primaryLanguage": {"name": "Python"},
                }
                for index in range(12)
            ]
            + [
                {
                    "name": f"other{index}",
                    "isFork": False,
                    "isArchived": False,
                    "stargazerCount": 0,
                    "pushedAt": None,
                    "primaryLanguage": {"name": language},
                }
                for index, language in enumerate(
                    ["TypeScript", "JavaScript", "Shell", "Swift", "SuperCollider"]
                )
            ]
        ),
        "contributions": {
            "total": 26_000,
            "commits": 13_000,
            "pull_requests": 2_200,
            "reviews": 100,
            "issues": 500,
            "restricted": 8_000,
        },
    }
    base.update(overrides)
    return base


def _report() -> Report:
    snapshot = _snapshot()
    return Report(
        login="tester",
        generated_at="2026-08-20T12:00:00Z",
        snapshot=snapshot,
        findings=run_all(snapshot),
        source_repository="organvm/laurea",
        source_sha="abc1234",
    )


def test_findings_are_measurements_or_transformations_not_rankings():
    findings = run_all(_snapshot())
    assert {finding.status for finding in findings} == {STATUS_MEASURED, STATUS_DERIVED}
    serialized = json.dumps([finding.to_dict() for finding in findings]).lower()
    rendered_evidence = json.dumps([finding.evidence for finding in findings]).lower()
    assert "percentile" not in serialized
    assert "top 1%" not in serialized
    assert "reviewed, mergeable" not in rendered_evidence
    assert "shipped units" not in rendered_evidence


def test_repository_visibility_is_not_attributed_as_individual_ownership():
    finding = next(item for item in run_all(_snapshot()) if item.axis == "repos_visible")
    assert finding.value == 17
    assert "visible" in finding.evidence.lower()
    assert "authorship" in finding.analysis.lower()


def test_forks_do_not_enter_the_visible_non_fork_count():
    snapshot = _snapshot()
    for repository in snapshot["repos"]:
        repository["isFork"] = True
    finding = next(item for item in run_all(snapshot) if item.axis == "repos_visible")
    assert finding.value == 0


@pytest.mark.parametrize(
    "repos",
    [None, [{}], [{"isFork": None}], ["repository"]],
)
def test_malformed_repository_entries_fail_closed(repos):
    with pytest.raises(ValueError, match="isFork"):
        run_all(_snapshot(repos=repos))


def test_rendered_assets_are_valid_and_wrap_bounded_hero_copy():
    assets = render_all(_report())
    assert "cards/hero.svg" in assets
    assert "PROFILE.md" in assets
    assert "SUPERLATIVES.md" not in assets
    for path, content in assets.items():
        if path.endswith(".svg"):
            root = ET.fromstring(content)
            assert root.tag.endswith("svg")
    hero = assets["cards/hero.svg"]
    assert "Measured GitHub activity profile" in hero
    assert "organization memberships" in hero
    assert hero.count("<tspan") >= 9
    rendered_text = " ".join(" ".join(ET.fromstring(hero).itertext()).split())
    assert PUBLIC_LIMITATION in rendered_text
    assert "Top 1%" not in hero


def test_profile_states_boundaries_and_never_duplicates_terminal_periods():
    profile = render_all(_report())["PROFILE.md"]
    assert "No percentile ranking is published" in profile
    assert "does not establish" in profile
    assert ".." not in profile


def test_compute_records_environment_provenance_and_utc_time(monkeypatch, tmp_path):
    snapshot = _snapshot(login="4444J99")
    monkeypatch.setattr("laurea.cli.resolve_token", lambda: "token")
    monkeypatch.setattr("laurea.cli.collect", lambda login, _auth: snapshot)
    monkeypatch.setattr("laurea.cli.collect_verdict", lambda *args: {"date": "2026-08-20"})
    monkeypatch.setattr("laurea.cli.append_entry", lambda *args: None)
    monkeypatch.setenv("GITHUB_REPOSITORY", "organvm/laurea")
    monkeypatch.setenv("GITHUB_SHA", "abc1234")

    report = _compute("4444J99", tmp_path)
    generated = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00"))
    assert generated.utcoffset().total_seconds() == 0
    assert report.source_repository == "organvm/laurea"
    assert report.source_sha == "abc1234"


def test_compute_and_legacy_load_use_honest_unknown_provenance(monkeypatch, tmp_path):
    snapshot = _snapshot()
    monkeypatch.setattr("laurea.cli.resolve_token", lambda: "token")
    monkeypatch.setattr("laurea.cli.collect", lambda login, _auth: snapshot)
    monkeypatch.setattr("laurea.cli.collect_verdict", lambda *args: {"date": "2026-08-20"})
    monkeypatch.setattr("laurea.cli.append_entry", lambda *args: None)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    report = _compute("tester", tmp_path)
    assert report.source_repository == "unknown"
    assert report.source_sha == "unknown"

    payload = report.to_dict()
    payload.pop("source_repository")
    payload.pop("source_sha")
    (tmp_path / "metrics.json").write_text(json.dumps(payload))
    loaded = _load(tmp_path)
    assert loaded.source_repository == "unknown"
    assert loaded.source_sha == "unknown"


def test_scheduled_workflow_selects_canonical_subject_without_breaking_forks():
    workflow = Path(".github/workflows/laurea.yml").read_text()
    assert "github.repository == 'organvm/laurea'" in workflow
    assert "github.repository_owner" in workflow
    assert 'laurea run --login "$LAUREA_LOGIN"' in workflow
