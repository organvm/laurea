"""The arena — comparable snapshots under one bounded field definition."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from .baselines import STATUS_MEASURED
from .models import Report

_MARK_START = "<!-- arena:rows:start -->"
_MARK_END = "<!-- arena:rows:end -->"

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
    rows.sort(key=lambda candidate: -candidate["contributions"])
    body = "".join(
        f"| {index + 1} | `@{candidate['login']}` | {candidate['contributions']:,} "
        f"| {candidate['prs']:,} | {candidate['repos']:,} | {candidate['languages']:,} "
        f"| {candidate['measured_axes']} | {candidate['verified']} |\n"
        for index, candidate in enumerate(rows)
    )
    text = f"{HEADER}{_MARK_START}\n{TABLE_HEAD}{body}{_MARK_END}\n"
    path.write_text(text)
    return text
