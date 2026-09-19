"""The arena — comparable snapshots under one bounded field definition."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .baselines import STATUS_MEASURED
from .models import Report
from .corpus import require_complete

_MARK_START = "<!-- arena:rows:start -->"
_MARK_END = "<!-- arena:rows:end -->"

_BASELINE_SOURCE = {
    "repository": "organvm/laurea",
    "commit": "90299a31cc77eccd0a5f2a33323f653683929e2b",
    "path": "LEADERBOARD.md",
    "sha256": "c7f60ffaff49478cc3430d36ae8ca93a566c655de3832d582a0d282a7b3a441e",
    "precision": "date-only",
}
_BASELINE_ROWS_SHA256 = (
    "cd8f38f91c9a97b57460ca54f5cc0d35475ed2f8c50971f73844a94da90786ee"
)

HEADER = """# THE ARENA — GitHub activity snapshots

Every row below was computed from the GitHub API at the recorded time.
Rows are comparable only under the same field definitions and token visibility.
They are not rankings of engineering quality, authorship, or impact.

"""

TABLE_HEAD = (
    "| # | login | contribution events | PRs opened | visible repos | languages | measured axes | verified |\n"
    "|---|-------|--------------------:|-----------:|--------------:|----------:|--------------:|----------|\n"
)


def build_row(report: Report) -> dict:
    """Build one leaderboard row from a report without adding rank claims."""

    require_complete(report.snapshot)

    def value(axis: str) -> int:
        finding = report.by_axis(axis)
        return int(finding.value) if finding else 0

    try:
        verified = datetime.fromisoformat(report.generated_at)
        verified_date = verified.astimezone(UTC).date().isoformat()
    except ValueError:
        verified_date = report.generated_at.split()[0]

    return {
        "login": report.login,
        "contributions": value("contributions_year"),
        "prs": value("pull_requests_year"),
        "repos": value("repos_visible"),
        "languages": value("language_breadth"),
        "measured_axes": sum(
            finding.status == STATUS_MEASURED for finding in report.findings
        ),
        "verified": verified_date,
    }


def _parse_rows(text: str) -> list[dict]:
    # Version 0.1 stored an unsupported percentile label in column seven and
    # used different repository semantics. Those rows cannot be relabeled as
    # v0.2 measurements; the next arena run safely starts a new table.
    if "| best floor |" in text:
        return []
    rows = []
    match = re.search(f"{_MARK_START}\n(.*?){_MARK_END}", text, re.DOTALL)
    if not match:
        return rows
    for line in match.group(1).splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 8 and cells[0].isdigit() and cells[6].isdigit():
            rows.append(
                {
                    "login": cells[1].strip("`@"),
                    "contributions": int(cells[2].replace(",", "")),
                    "prs": int(cells[3].replace(",", "")),
                    "repos": int(cells[4].replace(",", "")),
                    "languages": int(cells[5].replace(",", "")),
                    "measured_axes": int(cells[6]),
                    "verified": cells[7],
                }
            )
    return rows


def update_leaderboard(path: Path, row: dict) -> str:
    """Replace one login's row, order by activity count, and write the table."""
    rows = _parse_rows(path.read_text()) if path.exists() else []
    rows = [
        candidate
        for candidate in rows
        if candidate["login"].lower() != row["login"].lower()
    ]
    rows.append(row)
    text = _render_rows(rows)
    path.write_text(text)
    return text


def _render_rows(rows: list[dict]) -> str:
    rows.sort(key=lambda candidate: -candidate["contributions"])
    body = "".join(
        f"| {index + 1} | `@{candidate['login']}` | {candidate['contributions']:,} "
        f"| {candidate['prs']:,} | {candidate['repos']:,} | {candidate['languages']:,} "
        f"| {candidate['measured_axes']} | {candidate['verified']} |\n"
        for index, candidate in enumerate(rows)
    )
    text = f"{HEADER}{_MARK_START}\n{TABLE_HEAD}{body}{_MARK_END}\n"
    return text


def _validate_row(row: dict) -> None:
    if not isinstance(row, dict):
        raise ValueError("invalid activity row")
    login = row.get("login")
    if not isinstance(login, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", login):
        raise ValueError("invalid entrant identity")
    fields = {"login", "contributions", "prs", "repos", "languages", "measured_axes", "verified"}
    if set(row) != fields or any(type(row[k]) is not int or row[k] < 0 for k in fields - {"login", "verified"}):
        raise ValueError("invalid activity row")
    datetime.strptime(row["verified"], "%Y-%m-%d")


def write_entry(directory: Path, *, issue: int, row: dict, observed_at: str) -> Path:
    """Preserve one issue observation without rewriting another entrant's file."""
    if type(issue) is not int or issue <= 0:
        raise ValueError("positive issue identity required")
    _validate_row(row)
    stamp = datetime.fromisoformat(observed_at)
    if stamp.tzinfo is None:
        raise ValueError("observation requires a timezone")
    record = {"schema_version": 1, "issue": issue, "observed_at": observed_at, "row": row}
    payload = json.dumps(record, sort_keys=True, indent=2) + "\n"
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("entry directory must not be a symlink")
    target = directory / f"{issue}.json"
    if target.is_symlink():
        raise ValueError("entry must not be a symlink")
    fd, temporary = tempfile.mkstemp(prefix=".entry-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or target.read_text(encoding="utf-8") != payload:
                raise ValueError("issue observation already exists with different evidence") from None
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def materialize_entries(directory: Path, leaderboard: Path, *, baseline: Path | None = None) -> str:
    """Render accepted records deterministically; validate all before writing."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("entry directory unavailable")
    paths = sorted(directory.iterdir())
    if (not paths and baseline is None) or len(paths) > 10000:
        raise ValueError("entry inventory empty or exceeds bound")
    inherited = {}
    if baseline is not None:
        if baseline.is_symlink() or not baseline.is_file() or baseline.stat().st_size > 1000000:
            raise ValueError("invalid baseline file")
        data = json.loads(baseline.read_text())
        if (not isinstance(data, dict) or set(data) != {"schema_version", "source", "rows"}
                or type(data["schema_version"]) is not int or data["schema_version"] != 1
                or not isinstance(data["rows"], list) or len(data["rows"]) > 1000):
            raise ValueError("invalid baseline schema")
        source = data["source"]
        if source != _BASELINE_SOURCE:
            raise ValueError("invalid baseline provenance")
        rows_payload = json.dumps(data["rows"], sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(rows_payload).hexdigest() != _BASELINE_ROWS_SHA256:
            raise ValueError("historical baseline rows do not match pinned source")
        for row in data["rows"]:
            _validate_row(row)
            login = row["login"].lower()
            if login in inherited:
                raise ValueError("duplicate baseline login")
            inherited[login] = row
    records = []
    with tempfile.TemporaryDirectory() as scratch:
        validation = Path(scratch) / "validate"
        for path in paths:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 10000:
                raise ValueError("invalid entry file")
            record = json.loads(path.read_text())
            if (not isinstance(record, dict) or set(record) != {"schema_version", "issue", "observed_at", "row"}
                    or type(record["schema_version"]) is not int or record["schema_version"] != 1
                    or path.name != str(record["issue"]) + ".json"):
                raise ValueError("invalid entry schema or filename")
            write_entry(validation, issue=record["issue"], row=record["row"], observed_at=record["observed_at"])
            records.append(record)
        # Newest observation wins for one login; issue ID resolves timestamp ties.
        records.sort(key=lambda r: (datetime.fromisoformat(r["observed_at"]), r["issue"]))
        latest = dict(inherited)
        observed_logins = set()
        for record in records:
            row = record["row"]
            login = row["login"].lower()
            # Baseline has only a date. Never invent a timestamp or let an older
            # observation replace it; same-day precise observations supersede it.
            # Once an observation crosses that date-only boundary, its precise
            # observed_at order—not the row's date field—selects newer evidence.
            if (
                login in inherited
                and login not in observed_logins
                and row["verified"] < inherited[login]["verified"]
            ):
                continue
            latest[login] = row
            observed_logins.add(login)
        text = _render_rows([latest[login] for login in sorted(latest)])
    if leaderboard.is_symlink():
        raise ValueError("leaderboard must not be a symlink")
    leaderboard.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".leaderboard-", dir=leaderboard.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, leaderboard)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return text


def check_materialized_entries(directory: Path, leaderboard: Path, *, baseline: Path | None = None) -> None:
    """Reject a stale table without modifying any caller-owned output."""
    if leaderboard.is_symlink() or not leaderboard.is_file() or leaderboard.stat().st_size > 10000000:
        raise ValueError("bounded regular leaderboard required")
    with tempfile.TemporaryDirectory() as scratch:
        expected = materialize_entries(directory, Path(scratch) / "expected.md", baseline=baseline)
    if leaderboard.read_bytes() != expected.encode("utf-8"):
        raise ValueError("leaderboard is stale relative to accepted records")


def settlement_report(directory: Path, leaderboard: Path, *, baseline: Path | None = None) -> dict:
    """Report local row evidence; never infer default acceptance or close issues."""
    import hashlib
    # Freeze bounded inputs before validation so classification uses the same bytes.
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("entry directory unavailable")
    paths = sorted(directory.iterdir())
    if len(paths) > 10000:
        raise ValueError("entry inventory exceeds bound")
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        entries = root / "entries"; entries.mkdir()
        digests = {}
        for path in paths:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 10000:
                raise ValueError("invalid entry file")
            payload = path.read_bytes()
            if len(payload) > 10000:
                raise ValueError("entry exceeds bound")
            (entries / path.name).write_bytes(payload)
            digests[path.name] = hashlib.sha256(payload).hexdigest()
        copies = {}
        for name, path, limit in [("table.md", leaderboard, 10000000), ("baseline.json", baseline, 1000000)]:
            if path is None:
                continue
            if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
                raise ValueError("invalid settlement input")
            payload = path.read_bytes()
            if len(payload) > limit:
                raise ValueError("settlement input exceeds bound")
            copies[name] = root / name
            copies[name].write_bytes(payload)
            digests[name] = hashlib.sha256(payload).hexdigest()
        check_materialized_entries(entries, copies["table.md"], baseline=copies.get("baseline.json"))
        rows = {row["login"].lower(): row for row in _parse_rows(copies["table.md"].read_text())}
        observations = []
        for path in sorted(entries.iterdir()):
            record = json.loads(path.read_text())
            row = record["row"]
            observations.append({"issue": record["issue"], "login": row["login"],
                                 "local_disposition": "represented" if rows[row["login"].lower()] == row else "superseded_in_table"})
        return {"schema_version": 1, "scope": "local_snapshot", "default_acceptance": "unmeasured",
                "issue_closure": "human_owned", "input_sha256": digests,
                "observations": observations}
