import pytest

from laurea.pulls import collect_pulls

SHA = "a" * 40
BASE = "b" * 40
PREFIX = "/repos/owner/repo"


def fixture(*, draft=False, mergeable=True, move=None, denied=False, checks=None, reviews=None, count=1):
    calls = []
    def read(path):
        calls.append(path)
        if path == PREFIX + "/pulls?state=open&per_page=100":
            return [{"number": number} for number in range(1, count + 1)]
        if "/check-runs?" in path:
            if denied:
                raise OSError("private diagnostic")
            return checks if checks is not None else {"total_count": 0, "check_runs": []}
        if "/reviews?" in path:
            return reviews or []
        if "/pulls/" in path:
            number = int(path.rsplit("/", 1)[1])
            value = {"number": number, "state": "open", "draft": draft,
                     "mergeable": mergeable, "head": {"sha": SHA},
                     "base": {"sha": BASE, "ref": "main", "repo": {"id": 7}}}
            if calls.count(path) > 1 and move:
                if move in {"head", "base"}:
                    value[move]["sha"] = "c" * 40
                elif move == "closed":
                    value["state"] = "closed"
                else:
                    value["base"]["repo"]["id"] = 8
            return value
        raise AssertionError(path)
    return read, calls


@pytest.mark.parametrize("draft,mergeable,blocker", [(True, True, "draft"), (False, False, "merge_conflict")])
def test_current_generation_can_establish_specific_blocker(draft, mergeable, blocker):
    read, _ = fixture(draft=draft, mergeable=mergeable)
    row = collect_pulls(read, PREFIX, 7)["pulls_observed"][0]
    assert row["generation"] == "current"
    assert row["readiness"] == "blocked"
    assert row["blockers"] == [blocker]


@pytest.mark.parametrize("move", ["head", "base", "closed", "repository"])
def test_generation_changes_cannot_retain_readiness(move):
    read, _ = fixture(draft=True, move=move)
    row = collect_pulls(read, PREFIX, 7)["pulls_observed"][0]
    assert row["readiness"] == "unmeasured"
    assert row["generation"] != "current"


def test_empty_checks_do_not_prove_policy_or_acceptance():
    read, _ = fixture()
    row = collect_pulls(read, PREFIX, 7)["pulls_observed"][0]
    assert row["checks"]["observed"] == 0
    assert row["readiness"] == "unmeasured"
    assert row["checks"]["required_policy"] == "unmeasured"


@pytest.mark.parametrize("checks", [
    {"total_count": 2, "check_runs": []},
    {"total_count": 1, "check_runs": [{"head_sha": BASE, "status": "completed", "conclusion": "success"}]},
])
def test_truncated_or_wrong_head_checks_are_unknown(checks):
    read, _ = fixture(checks=checks)
    assert collect_pulls(read, PREFIX, 7)["pulls_observed"][0]["checks"] == {"status": "unmeasured"}


def test_denial_keeps_current_identity_but_not_check_coverage():
    read, _ = fixture(denied=True)
    result = collect_pulls(read, PREFIX, 7)
    row = result["pulls_observed"][0]
    assert result["status"] == "unmeasured"
    assert result["pulls_unmeasured"] == 1
    assert row["generation"] == "current"
    assert row["checks"] == {"status": "unmeasured"}
    assert "private diagnostic" not in str(row)


def test_reviews_are_bound_to_head_and_deduplicated_by_reviewer():
    reviews = [
        {"id": 99, "commit_id": SHA, "user": {"id": 4}, "state": "APPROVED"},
        {"id": 2, "commit_id": SHA, "user": {"id": 4}, "state": "CHANGES_REQUESTED"},
        {"id": 3, "commit_id": SHA, "user": {"id": 4}, "state": "COMMENTED"},
        {"id": 4, "commit_id": BASE, "user": {"id": 5}, "state": "APPROVED"},
    ]
    read, _ = fixture(reviews=reviews)
    row = collect_pulls(read, PREFIX, 7)["pulls_observed"][0]["reviews"]
    assert row["current_head_approvals"] == 0
    assert row["current_head_changes_requested"] == 1
    assert row["other_head_reviews"] == 1


def test_detail_budget_preserves_omitted_denominator():
    read, calls = fixture(count=8)
    result = collect_pulls(read, PREFIX, 7)
    assert result["open_observed"] == 8
    assert len(result["pulls_observed"]) == 5
    assert result["pulls_unmeasured"] == 3
    assert len(calls) == 21


def test_readback_budget_failure_never_reports_a_current_blocker():
    base, calls = fixture(draft=True)
    def read(path):
        if path == PREFIX + "/pulls/1" and path in calls:
            raise RuntimeError("budget exhausted")
        return base(path)
    row = collect_pulls(read, PREFIX, 7)["pulls_observed"][0]
    assert row["status"] == "unmeasured"
    assert row["generation"] == "unmeasured"
    assert row["readiness"] == "unmeasured"


def test_failed_optional_check_is_observed_without_inventing_merge_policy():
    checks = {"total_count": 1, "check_runs": [
        {"head_sha": SHA, "status": "completed", "conclusion": "failure"}]}
    read, _ = fixture(checks=checks)
    row = collect_pulls(read, PREFIX, 7)["pulls_observed"][0]
    assert row["checks"]["failing"] == 1
    assert row["readiness"] == "unmeasured"


def test_closed_detail_cannot_complete_open_listing_coverage():
    base, _ = fixture()
    def read(path):
        result = base(path)
        if path == PREFIX + "/pulls/1":
            result["state"] = "closed"
        return result
    result = collect_pulls(read, PREFIX, 7)
    assert result["pulls_observed"][0]["generation"] == "current"
    assert result["pulls_observed"][0]["checks"]["status"] == "measured"
    assert result["status"] == "unmeasured"
    assert result["pulls_unmeasured"] == 1
