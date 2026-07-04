"""Verdict meter: idempotent history, delta math, valid card."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from laurea.verdict import append_entry, deltas, load_history, verdict_card


def test_append_is_idempotent_per_date(tmp_path):
    jsonl = tmp_path / "verdict.jsonl"
    append_entry({"date": "2026-07-04", "followers": 38, "stars_estate": 56}, jsonl)
    history = append_entry({"date": "2026-07-04", "followers": 39, "stars_estate": 56}, jsonl)
    assert len(history) == 1
    assert history[0]["followers"] == 39  # same-day rerun overwrites, never duplicates


def test_deltas_against_oldest_entry(tmp_path):
    jsonl = tmp_path / "verdict.jsonl"
    append_entry({"date": "2026-07-04", "followers": 38, "stars_estate": 56}, jsonl)
    history = append_entry({"date": "2026-07-18", "followers": 52, "stars_estate": 90}, jsonl)
    assert deltas(history, "followers") == (52, 14)
    assert deltas(history, "stars_estate") == (90, 34)
    assert deltas(history, "views_14d") == (None, None)  # absent signal stays silent


def test_single_entry_is_baseline_not_delta(tmp_path):
    jsonl = tmp_path / "verdict.jsonl"
    history = append_entry({"date": "2026-07-04", "followers": 38}, jsonl)
    assert deltas(history, "followers") == (38, None)
    assert load_history(jsonl) == history


def test_verdict_card_is_valid_svg(tmp_path):
    jsonl = tmp_path / "verdict.jsonl"
    append_entry({"date": "2026-07-04", "followers": 38, "stars_estate": 56,
                  "showcase_stars": 0, "unique_visitors_14d": 0}, jsonl)
    history = append_entry({"date": "2026-07-18", "followers": 52, "stars_estate": 90,
                            "showcase_stars": 41, "unique_visitors_14d": 900}, jsonl)
    svg = verdict_card(history)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "THE VERDICT METER" in svg and "+34" in svg and "+14" in svg
