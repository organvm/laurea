import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from laurea.arena import write_entry

STAMP = "2026-09-16T07:00:00+00:00"
def row(login):
    return dict(login=login, contributions=1, prs=2, repos=3, languages=1, measured_axes=4, verified="2026-09-16")

def test_concurrent_entrants_preserve_both_observations(tmp_path):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(write_entry, tmp_path, issue=i, row=row(login), observed_at=STAMP)
                   for i, login in [(1, "alice"), (2, "bob")]]
        paths = [f.result() for f in futures]
    assert {json.loads(p.read_text())["row"]["login"] for p in paths} == {"alice", "bob"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["1.json", "2.json"]

def test_replay_is_idempotent_but_changed_evidence_cannot_overwrite(tmp_path):
    path = write_entry(tmp_path, issue=1, row=row("alice"), observed_at=STAMP)
    original = path.read_bytes()
    assert write_entry(tmp_path, issue=1, row=row("alice"), observed_at=STAMP) == path
    with pytest.raises(ValueError):
        write_entry(tmp_path, issue=1, row=row("bob"), observed_at=STAMP)
    assert path.read_bytes() == original

@pytest.mark.parametrize("issue,login", [(0,"alice"),(True,"alice"),(1,"../outside"),(1,"")])
def test_invalid_identity_cannot_create_entry(tmp_path, issue, login):
    with pytest.raises(ValueError):
        write_entry(tmp_path, issue=issue, row=row(login), observed_at=STAMP)
    assert not list(tmp_path.iterdir())

def test_symlink_destination_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.write_text("preserve")
    (tmp_path / "1.json").symlink_to(outside)
    with pytest.raises(ValueError):
        write_entry(tmp_path, issue=1, row=row("alice"), observed_at=STAMP)
    assert outside.read_text() == "preserve"


def test_cli_issue_mode_preserves_existing_table(tmp_path, monkeypatch):
    from laurea import cli
    monkeypatch.setattr(cli, "resolve_token", lambda: "fixture")
    monkeypatch.setattr(cli, "collect", lambda *a: {})
    monkeypatch.setattr(cli, "run_all", lambda *a: [])
    monkeypatch.setattr(cli, "build_row", lambda report: row(report.login))
    table = tmp_path / "LEADERBOARD.md"
    table.write_text("existing table")
    entries = tmp_path / "entries"
    assert cli.main(["arena", "--login", "alice", "--issue", "12", "--entries", str(entries), "--leaderboard", str(table)]) == 0
    assert table.read_text() == "existing table"
    assert json.loads((entries / "12.json").read_text())["row"]["login"] == "alice"


def test_cli_rejects_invalid_issue_before_collection(monkeypatch):
    from laurea import cli
    monkeypatch.setattr(cli, "collect", lambda *a: pytest.fail("must not collect"))
    with pytest.raises(SystemExit):
        cli.main(["arena", "--login", "alice", "--issue", "0"])


def test_materialization_preserves_entrants_and_selects_latest_observation(tmp_path):
    from laurea.arena import materialize_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=2, row=row("bob"), observed_at=STAMP)
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    newer = row("alice"); newer["contributions"] = 9
    write_entry(entries, issue=3, row=newer, observed_at="2026-09-17T00:00:00Z")
    table = tmp_path / "table.md"
    text = materialize_entries(entries, table)
    assert text.count("@alice") == text.count("@bob") == 1
    assert "`@alice` | 9" in text
    assert materialize_entries(entries, table) == text


def test_malformed_record_preserves_previous_table(tmp_path):
    from laurea.arena import materialize_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    (entries / "2.json").write_text("{}")
    table = tmp_path / "table.md"; table.write_text("preserve")
    with pytest.raises(ValueError):
        materialize_entries(entries, table)
    assert table.read_text() == "preserve"


def test_historical_baseline_matches_committed_source():
    import hashlib
    from pathlib import Path
    from laurea.arena import _parse_rows
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / "arena/baseline.json").read_text())
    source = baseline["source"]
    raw = (root / "arena/baseline-source.md").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source["sha256"]
    assert _parse_rows(raw.decode()) == baseline["rows"]
    assert source["precision"] == "date-only"


def test_baseline_survives_new_entrants_and_older_observations(tmp_path):
    from pathlib import Path
    from laurea.arena import materialize_entries
    baseline = Path(__file__).resolve().parents[1] / "arena/baseline.json"
    entries = tmp_path / "entries"; entries.mkdir()
    table = tmp_path / "table.md"
    assert "`@4444J99` | 33,587" in materialize_entries(entries, table, baseline=baseline)
    older = row("4444J99"); older["verified"] = "2026-08-20"
    write_entry(entries, issue=1, row=older, observed_at="2026-08-20T00:00:00Z")
    write_entry(entries, issue=2, row=row("alice"), observed_at=STAMP)
    text = materialize_entries(entries, table, baseline=baseline)
    assert "`@4444J99` | 33,587" in text and "@alice" in text
    write_entry(entries, issue=3, row=row("4444J99"), observed_at=STAMP)
    assert "`@4444J99` | 1" in materialize_entries(entries, table, baseline=baseline)


def test_newest_observation_wins_after_crossing_date_only_baseline(tmp_path):
    from pathlib import Path
    from laurea.arena import materialize_entries

    baseline = Path(__file__).resolve().parents[1] / "arena/baseline.json"
    entries = tmp_path / "entries"
    first = row("4444J99")
    first["contributions"] = 9
    first["verified"] = "2026-09-17"
    newest = row("4444J99")
    newest["contributions"] = 12
    newest["verified"] = "2026-09-15"
    write_entry(entries, issue=1, row=first, observed_at="2026-09-17T00:00:00Z")
    write_entry(entries, issue=2, row=newest, observed_at="2026-09-18T00:00:00Z")

    text = materialize_entries(entries, tmp_path / "table.md", baseline=baseline)
    assert "`@4444J99` | 12" in text
    assert "`@4444J99` | 9" not in text


def test_baseline_rows_cannot_be_rewritten_with_mutable_provenance(tmp_path):
    from pathlib import Path
    from laurea.arena import materialize_entries

    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / "arena/baseline.json").read_text())
    baseline["rows"][0]["contributions"] += 1
    forged = tmp_path / "baseline.json"
    forged.write_text(json.dumps(baseline))
    entries = tmp_path / "entries"
    entries.mkdir()

    with pytest.raises(ValueError, match="pinned source"):
        materialize_entries(entries, tmp_path / "table.md", baseline=forged)


def test_newly_accepted_entrant_invalidates_old_table_without_mutation(tmp_path):
    from laurea.arena import materialize_entries, check_materialized_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    table = tmp_path / "table.md"
    materialize_entries(entries, table)
    check_materialized_entries(entries, table)
    previous = table.read_bytes()
    write_entry(entries, issue=2, row=row("bob"), observed_at=STAMP)
    with pytest.raises(ValueError, match="stale"):
        check_materialized_entries(entries, table)
    assert table.read_bytes() == previous
    materialize_entries(entries, table)
    check_materialized_entries(entries, table)
    assert "@alice" in table.read_text() and "@bob" in table.read_text()


def test_cli_check_is_read_only(tmp_path):
    from laurea import cli
    from laurea.arena import materialize_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    table = tmp_path / "table.md"
    materialize_entries(entries, table)
    before = table.stat().st_mtime_ns
    assert cli.main(["arena-table", "--entries", str(entries), "--leaderboard", str(table), "--check"]) == 0
    assert table.stat().st_mtime_ns == before


def test_settlement_report_preserves_obligations_and_binds_snapshot(tmp_path):
    from laurea.arena import materialize_entries, settlement_report
    entries = tmp_path / "entries"
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    newer = row("alice"); newer["contributions"] = 9
    write_entry(entries, issue=2, row=newer, observed_at="2026-09-17T00:00:00Z")
    table = tmp_path / "table.md"
    materialize_entries(entries, table)
    before = table.read_bytes()
    report = settlement_report(entries, table)
    assert report["default_acceptance"] == "unmeasured"
    assert report["issue_closure"] == "human_owned"
    assert [item["local_disposition"] for item in report["observations"]] == ["superseded_in_table", "represented"]
    assert set(report["input_sha256"]) == {"1.json", "2.json", "table.md"}
    assert table.read_bytes() == before
    table.write_text("stale")
    with pytest.raises(ValueError, match="stale"):
        settlement_report(entries, table)


def test_cli_settlement_report_is_json_without_publication_claim(tmp_path, capsys):
    from laurea import cli
    from laurea.arena import materialize_entries
    entries = tmp_path / "entries"
    write_entry(entries, issue=1, row=row("alice"), observed_at=STAMP)
    table = tmp_path / "table.md"
    materialize_entries(entries, table)
    assert cli.main(["arena-table", "--entries", str(entries), "--leaderboard", str(table), "--settlement-report"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["scope"] == "local_snapshot"
    assert report["observations"][0]["issue"] == 1
