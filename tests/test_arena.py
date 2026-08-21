"""Arena rows remain comparable without implying an engineering rank."""

from __future__ import annotations

from laurea.arena import build_row, update_leaderboard
from laurea.detectors import run_all
from laurea.models import Report


def _report(
    login="tester", contributions=26_000, generated_at="2026-07-05T23:30:00-04:00"
):
    snapshot = {
        "login": login,
        "name": login,
        "created_at": "2016-12-27T17:24:06Z",
        "followers": 1,
        "orgs": [],
        "repos": [
            {
                "name": "r",
                "isFork": False,
                "isArchived": False,
                "stargazerCount": 0,
                "pushedAt": None,
                "primaryLanguage": {"name": "Python"},
            }
        ],
        "contributions": {
            "total": contributions,
            "commits": 1,
            "pull_requests": 1,
            "reviews": 0,
            "issues": 0,
            "restricted": 0,
        },
    }
    return Report(
        login=login,
        generated_at=generated_at,
        snapshot=snapshot,
        findings=run_all(snapshot),
    )


def test_row_uses_utc_date_and_measured_axis_count():
    row = build_row(_report())
    assert row["verified"] == "2026-07-06"
    assert row["measured_axes"] == 4
    assert row["contributions"] == 26_000


def test_leaderboard_orders_activity_and_deduplicates(tmp_path):
    leaderboard = tmp_path / "LEADERBOARD.md"
    update_leaderboard(leaderboard, build_row(_report("alice", 100)))
    update_leaderboard(leaderboard, build_row(_report("bob", 9_000)))
    text = update_leaderboard(leaderboard, build_row(_report("alice", 200)))
    assert text.index("bob") < text.index("alice")
    assert text.count("@alice") == 1
    assert "not rankings of engineering quality" in text


def test_leaderboard_discards_incompatible_v1_rank_rows(tmp_path):
    leaderboard = tmp_path / "LEADERBOARD.md"
    leaderboard.write_text(
        "<!-- arena:rows:start -->\n"
        "| # | login | contributions/yr | PRs/yr | repos | languages | best floor | verified |\n"
        "| 1 | `@legacy` | 1,000 | 20 | 30 | 4 | top 0.1% | 2026-07-05 |\n"
        "<!-- arena:rows:end -->\n"
    )
    text = update_leaderboard(leaderboard, build_row(_report("current", 200)))
    assert "@legacy" not in text
    assert "top 0.1%" not in text
    assert "@current" in text
