"""Counts-only alert observations; neither scanner coverage nor severity is inferred."""
from __future__ import annotations

from typing import Any


def summarize_alerts(rows: Any, source: str) -> dict:
    if not isinstance(rows, list):
        raise ValueError("malformed alert list")
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or type(row.get("number")) is not int
                or row["number"] <= 0 or row["number"] in seen or row.get("state") != "open"):
            raise ValueError("alert identity or state unavailable")
        seen.add(row["number"])
    complete = len(rows) < 100
    result = {
        "status": "measured" if complete else "unmeasured",
        "open_alerts_observed": len(rows), "complete": complete,
        "coverage": "unmeasured",
        "scope": "Repository-wide open alerts at observation time; not exact-default-SHA coverage.",
        "boundary": "An empty alert list does not establish enabled scanners, current scans, or required security policy.",
    }
    if source == "secret_scanning":
        # Do not export secrets, locations, detector names, validity or account metadata.
        result["credential_alerts_observed"] = len(rows)
        return result
    fields = {"dependabot": ("security_vulnerability", "severity"),
              "code_scanning": ("rule", "security_severity_level")}
    if source not in fields:
        raise ValueError("unknown alert source")
    parent, field = fields[source]
    counts = dict.fromkeys(("critical", "high", "medium", "low", "unmeasured"), 0)
    for row in rows:
        detail = row.get(parent)
        severity = detail.get(field) if isinstance(detail, dict) else None
        if not isinstance(severity, str) or severity not in counts or severity == "unmeasured":
            severity = "unmeasured"
        counts[severity] += 1
    result["severity_counts_observed"] = counts
    result["severity_status"] = "measured" if complete and not counts["unmeasured"] else "unmeasured"
    return result
