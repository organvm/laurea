"""Tests: floor logic, detector conjunction honesty, valid SVG output."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from laurea.baselines import BASELINES, TIER_TOP_01, TIER_TOP_1, TIER_NOTABLE
from laurea.detectors import run_all
from laurea.models import Report
from laurea.render import render_all


def _snapshot(**overrides):
    base = {
        "login": "tester",
        "name": "Tester",
        "created_at": "2016-12-27T17:24:06Z",
        "followers": 38,
        "orgs": [f"org{i}" for i in range(10)],
        "repos": (
            [{"name": f"py{i}", "isFork": False, "isArchived": False,
              "stargazerCount": 1, "pushedAt": None,
              "primaryLanguage": {"name": "Python"}} for i in range(120)]
            + [{"name": f"ts{i}", "isFork": False, "isArchived": False,
                "stargazerCount": 0, "pushedAt": None,
                "primaryLanguage": {"name": lang}} for i, lang in enumerate(
                    ["TypeScript"] * 60 + ["JavaScript"] * 10 + ["Shell"] * 6
                    + ["Swift", "Kotlin", "Astro", "HTML", "SuperCollider",
                       "G-code", "CSS", "Ruby"])]
        ),
        "contributions": {
            "total": 26_000, "commits": 13_000, "pull_requests": 2_200,
            "reviews": 100, "issues": 500, "restricted": 8_000,
        },
    }
    base.update(overrides)
    return base


def test_floors_are_conservative_and_ordered():
    for base in BASELINES.values():
        thresholds = [t for t, _ in base.floors]
        assert thresholds == sorted(thresholds, reverse=True), base.axis
        assert base.source and base.method, base.axis


def test_tier_for_reads_first_cleared_floor():
    b = BASELINES["contributions_year"]
    assert b.tier_for(26_000) == TIER_TOP_01
    assert b.tier_for(6_000) == TIER_TOP_1
    assert b.tier_for(10) == TIER_NOTABLE


def test_composite_renders_when_all_legs_clear():
    findings = run_all(_snapshot())
    composite = [f for f in findings if f.axis == "composite_python_full_stack"]
    assert len(composite) == 1
    assert composite[0].tier == TIER_TOP_1


def test_composite_deletes_itself_when_a_leg_fails():
    weak = _snapshot()
    weak["contributions"] = dict(weak["contributions"], total=800)
    findings = run_all(weak)
    assert not [f for f in findings if f.axis == "composite_python_full_stack"]


def test_composite_requires_python_led_corpus():
    js_led = _snapshot()
    for repo in js_led["repos"][:200]:
        repo["primaryLanguage"] = {"name": "JavaScript"}
    findings = run_all(js_led)
    assert not [f for f in findings if f.axis == "composite_python_full_stack"]


def test_forks_do_not_count_toward_portfolio():
    forked = _snapshot()
    for repo in forked["repos"]:
        repo["isFork"] = True
    findings = run_all(forked)
    repos = next(f for f in findings if f.axis == "repos_owned")
    assert repos.value == 0


def test_rendered_svgs_are_valid_xml_with_animation():
    snapshot = _snapshot()
    report = Report(
        login="tester", generated_at="2026-07-04 00:00 UTC",
        snapshot=snapshot, findings=run_all(snapshot),
    )
    assets = render_all(report)
    svgs = [k for k in assets if k.endswith(".svg")]
    assert "cards/hero.svg" in svgs and len(svgs) >= 6
    for key in svgs:
        root = ET.fromstring(assets[key])  # raises on invalid XML
        assert root.tag.endswith("svg")
        assert "animate" in assets[key] or "@keyframes" in assets[key]
    assert "Top 1% GitHub output profile" in assets["cards/hero.svg"]
    assert "TOP 0.1% ENGINEERING THROUGHPUT" not in assets["cards/hero.svg"]
    assert "output profile" in assets["cards/hero.svg"]
    assert "GitHub contributions · trailing 12 months" in assets["cards/hero.svg"]
    assert "non-fork repositories visible to this run" in assets["cards/hero.svg"]
    assert "pull requests opened · trailing 12 months" in assets["cards/hero.svg"]
    assert "organizations queried" in assets["cards/hero.svg"]
    assert "does not establish quality, reliability, adoption, or business impact" in assets["cards/hero.svg"]
    assert "METHODOLOGY.md" in assets["SUPERLATIVES.md"]
    assert "do not establish" in assets["SUPERLATIVES.md"]


def test_every_measured_finding_carries_analysis():
    for f in run_all(_snapshot()):
        assert f.analysis, f"{f.axis} rendered without analysis — a datum needs context"


def test_superlatives_translate_tiers_into_odds():
    snapshot = _snapshot()
    report = Report(
        login="tester", generated_at="2026-07-04 00:00 UTC",
        snapshot=snapshot, findings=run_all(snapshot),
    )
    md = render_all(report)["SUPERLATIVES.md"]
    assert "at least 1 in 1,000" in md and "What this means:" in md
    assert "at most ~30,000 people" in md and "The denominators" in md


def test_cohort_math_is_floor_times_population():
    from laurea.baselines import cohort_for
    n, anchor = cohort_for("top 0.1%")
    assert n == 30_000 and "stadium" in anchor
    n, _ = cohort_for("top 1%")
    assert n == 300_000
    assert cohort_for("notable") is None


def test_scheduled_workflow_tracks_the_declared_subject():
    workflow = Path(".github/workflows/laurea.yml").read_text()
    assert 'laurea run --login "4444J99"' in workflow
    assert "github.repository_owner" not in workflow


def test_report_contract_carries_source_and_subject_identity():
    snapshot = _snapshot(login="4444J99")
    report = Report(
        login="4444J99",
        generated_at="2026-08-20T12:00:00Z",
        snapshot=snapshot,
        findings=run_all(snapshot),
        source_repository="organvm/laurea",
        source_sha="abc123",
    ).to_dict()
    assert report["login"] == report["snapshot"]["login"] == "4444J99"
    assert report["generated_at"].endswith("Z")
    assert report["source_repository"] == "organvm/laurea"
    assert report["source_sha"] == "abc123"
