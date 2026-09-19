import json

import pytest

from laurea.health import collect_health_batch


def test_bounded_batch_keeps_full_denominator_and_redacts_private_entries():
    calls = []
    def read(path):
        calls.append(path)
        return {"private": True}
    report = collect_health_batch(["private/one", "private/two", "private/three"],
                                  "fixture", limit=2, read=read)
    assert len(calls) == 2
    assert report["scope"]["inventory_entries"] == 3
    assert report["scope"]["entries_not_attempted"] == 1
    assert report["scope"]["private_entries_excluded"] == 2
    assert "private/" not in json.dumps(report)
    assert report["status"] == "unmeasured"


@pytest.mark.parametrize("inventory", [[], ["owner/repo", "OWNER/REPO"], [None], "owner/repo"])
def test_invalid_inventory_does_not_read(inventory):
    def read(path):
        raise AssertionError("must not perform reads")
    with pytest.raises(ValueError):
        collect_health_batch(inventory, "fixture", read=read)


def test_budget_failure_preserves_unknown_entries():
    def read(path):
        raise OSError("PRIVATE_TOKEN_DETAIL")
    report = collect_health_batch(["owner/one", "owner/two"], "fixture", read=read)
    assert report["scope"]["attempted_entries_unmeasured"] == 2
    assert report["scope"]["private_entries_excluded"] == 0
    assert "PRIVATE_TOKEN_DETAIL" not in json.dumps(report)


def test_offset_preserves_inventory_without_repeating_earlier_reads():
    calls = []
    def read(path):
        calls.append(path)
        return {"private": True}
    report = collect_health_batch(["owner/one", "owner/two", "owner/three"],
                                  "fixture", offset=1, limit=1, read=read)
    assert calls == ["/repos/owner/two"]
    assert report["scope"]["inventory_entries"] == 3
    assert report["scope"]["entries_not_attempted"] == 2
    assert report["scope"]["selection_offset"] == 1
    assert report["scope"]["selection_end_exclusive"] == 2


@pytest.mark.parametrize("offset", [-1, True, 1, "0"])
def test_invalid_offset_is_rejected_before_reads(offset):
    with pytest.raises(ValueError):
        collect_health_batch(["owner/one"], "fixture", offset=offset,
                             read=lambda path: pytest.fail("unexpected read"))


def test_one_reader_budget_is_shared(monkeypatch):
    instances = []
    class Limited:
        def __init__(self, token):
            instances.append(self)
            self.calls = 0
        def __call__(self, path):
            self.calls += 1
            if self.calls > 1:
                raise OSError("budget exhausted")
            return {"private": True}
    monkeypatch.setattr("laurea.health.Reader", Limited)
    report = collect_health_batch(["owner/one", "owner/two"], "fixture")
    assert len(instances) == 1
    assert report["scope"]["private_entries_excluded"] == 1
    assert report["scope"]["attempted_entries_unmeasured"] == 1


def test_cli_emits_explicit_unmeasured_batch(tmp_path, monkeypatch, capsys):
    from laurea.cli import main
    source = tmp_path / "inventory.json"
    source.write_text('["owner/repo"]')
    monkeypatch.setattr("laurea.cli.resolve_token", lambda: "fixture")
    monkeypatch.setattr("laurea.cli.collect_health_batch", lambda *args, **kwargs: {
        "status": "unmeasured", "scope": {"inventory_entries": 1}})
    assert main(["health-batch", "--inventory", str(source), "--limit", "1"]) == 77
    assert json.loads(capsys.readouterr().out)["scope"]["inventory_entries"] == 1
