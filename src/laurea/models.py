"""Data shapes shared by the collector, detectors, and renderer."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Finding:
    """One measured axis of engineering output.

    ``tier`` is a conservative percentile *floor* ("top 0.1%", "top 1%",
    "top 5%", "notable") — never a point estimate. ``evidence`` is the
    exact measured value in words; ``source`` cites the baseline the
    floor was read from; ``analysis`` translates the number into human
    scale — a datum without analysis is noise, so every finding carries
    its own context.
    """

    axis: str
    title: str
    value: float
    unit: str
    tier: str
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "login": self.login,
            "generated_at": self.generated_at,
            "snapshot": self.snapshot,
            "findings": [f.to_dict() for f in self.findings],
        }

    def by_axis(self, axis: str) -> Finding | None:
        for f in self.findings:
            if f.axis == axis:
                return f
        return None
