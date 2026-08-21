"""Data shapes shared by the collector, detectors, and renderer."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Finding:
    """One bounded observation derived from a GitHub API snapshot.

    ``status`` distinguishes direct API measurements from deterministic
    transformations. It is not a percentile, quality grade, or ranking.
    ``source`` names the exact field or transformation and ``analysis``
    states what the observation does and does not establish.
    """

    axis: str
    title: str
    value: float
    unit: str
    status: str
    evidence: str
    source: str
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Report:
    """The full output of one compute run."""

    login: str
    generated_at: str
    snapshot: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    source_repository: str = "unknown"
    source_sha: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "laurea.report.v2",
            "login": self.login,
            "generated_at": self.generated_at,
            "source_repository": self.source_repository,
            "source_sha": self.source_sha,
            "snapshot": self.snapshot,
            "findings": [f.to_dict() for f in self.findings],
        }

    def by_axis(self, axis: str) -> Finding | None:
        for f in self.findings:
            if f.axis == axis:
                return f
        return None
