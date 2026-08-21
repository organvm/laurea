"""Observation classifications retained under the legacy module name.

LAVREA previously published heuristic percentile floors from this module.
Those floors were not backed by a population distribution and are no longer
part of the public contract. Findings now distinguish direct measurements
from deterministic transformations only.
"""

STATUS_MEASURED = "measured"
STATUS_DERIVED = "derived"

_STATUS_ORDER = (STATUS_MEASURED, STATUS_DERIVED)


def status_rank(status: str) -> int:
    """Return a stable display order without implying quality or rank."""
    return _STATUS_ORDER.index(status)
