"""laurea — compute | render | run | axes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .baselines import STATUS_DERIVED, STATUS_MEASURED
from .detectors import REGISTRY, run_all
from .github import collect, resolve_token
from .models import Finding, Report
from .arena import build_row, update_leaderboard
from .render import render_all
from .verdict import append_entry, collect_verdict, load_history, verdict_card

_REPORT_SCHEMA = "laurea.report.v2"
_FINDING_STATUSES = {STATUS_MEASURED, STATUS_DERIVED}
_LEGACY_GENERATED_PATHS = (
    "SUPERLATIVES.md",
    "cards/repos_owned.svg",
    "cards/orgs_operated.svg",
    "cards/full_stack_coverage.svg",
)


def _compute(login: str, assets: Path) -> Report:
    token = resolve_token()
    snapshot = collect(login, token)
    now = datetime.now(timezone.utc)
    report = Report(
        login=login,
        generated_at=now.isoformat().replace("+00:00", "Z"),
        snapshot=snapshot,
        findings=run_all(snapshot),
        source_repository=os.environ.get("GITHUB_REPOSITORY", "unknown"),
        source_sha=os.environ.get("GITHUB_SHA", "unknown"),
    )
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "metrics.json").write_text(json.dumps(report.to_dict(), indent=2))
    showcase = os.environ.get("GITHUB_REPOSITORY", f"{login}/laurea")
    entry = collect_verdict(snapshot, showcase, token, now.strftime("%Y-%m-%d"))
    append_entry(entry, assets / "verdict.jsonl")
    return report


def _load(assets: Path) -> Report:
    data = json.loads((assets / "metrics.json").read_text())
    schema_version = data.get("schema_version")
    if schema_version != _REPORT_SCHEMA:
        raise ValueError(
            f"unsupported metrics schema {schema_version!r}; recompute with the current LAVREA release"
        )
    findings = data.get("findings")
    if not isinstance(findings, list) or any(
        not isinstance(finding, dict) or finding.get("status") not in _FINDING_STATUSES
        for finding in findings
    ):
        raise ValueError("metrics findings must use measured or derived status values")
    return Report(
        login=data["login"],
        generated_at=data["generated_at"],
        snapshot=data["snapshot"],
        findings=[Finding(**finding) for finding in findings],
        source_repository=data.get("source_repository", "unknown"),
        source_sha=data.get("source_sha", "unknown"),
    )


def _render(report: Report, assets: Path) -> list[str]:
    out = render_all(report)
    history = load_history(assets / "verdict.jsonl")
    if history:
        out["cards/verdict.svg"] = verdict_card(history)
    written = []
    for rel, content in out.items():
        path = assets / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written.append(str(path))
    for relative_path in _LEGACY_GENERATED_PATHS:
        legacy_path = assets / relative_path
        if legacy_path.exists():
            legacy_path.unlink()
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="laurea", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("compute", "render", "run"):
        p = sub.add_parser(name)
        p.add_argument("--login", required=(name != "render"))
        p.add_argument("--assets", default="assets", type=Path)
    sub.add_parser("axes")
    arena = sub.add_parser("arena")
    arena.add_argument("--login", required=True)
    arena.add_argument("--leaderboard", default="LEADERBOARD.md", type=Path)

    args = parser.parse_args(argv)
    if args.cmd == "arena":
        snapshot = collect(args.login, resolve_token())
        report = Report(
            login=args.login,
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            snapshot=snapshot,
            findings=run_all(snapshot),
        )
        update_leaderboard(args.leaderboard, build_row(report))
        print(f"arena: verified @{args.login} -> {args.leaderboard}")
        return 0

    if args.cmd == "axes":
        for det in REGISTRY:
            print(f"{det.__name__}: {(det.__doc__ or '').strip() or 'axis detector'}")
        return 0

    if args.cmd in ("compute", "run"):
        report = _compute(args.login, args.assets)
        print(f"computed {len(report.findings)} findings for @{args.login}")
        for f in report.findings:
            value = f"{int(f.value):,}" if f.value == int(f.value) else f"{f.value:,.1f}"
            print(f"  [{f.status:>8}] {f.title}: {value} {f.unit}")
    else:
        report = _load(args.assets)

    if args.cmd in ("render", "run"):
        for path in _render(report, args.assets):
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
