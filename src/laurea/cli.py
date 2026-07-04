"""laurea — compute | render | run | axes."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .detectors import REGISTRY, run_all
from .github import collect
from .models import Finding, Report
from .render import render_all


def _compute(login: str, assets: Path) -> Report:
    snapshot = collect(login)
    report = Report(
        login=login,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        snapshot=snapshot,
        findings=run_all(snapshot),
    )
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "metrics.json").write_text(json.dumps(report.to_dict(), indent=2))
    return report


def _load(assets: Path) -> Report:
    data = json.loads((assets / "metrics.json").read_text())
    return Report(
        login=data["login"],
        generated_at=data["generated_at"],
        snapshot=data["snapshot"],
        findings=[Finding(**f) for f in data["findings"]],
    )


def _render(report: Report, assets: Path) -> list[str]:
    written = []
    for rel, content in render_all(report).items():
        path = assets / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written.append(str(path))
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

    args = parser.parse_args(argv)
    if args.cmd == "axes":
        for det in REGISTRY:
            print(f"{det.__name__}: {(det.__doc__ or '').strip() or 'axis detector'}")
        return 0

    if args.cmd in ("compute", "run"):
        report = _compute(args.login, args.assets)
        print(f"computed {len(report.findings)} findings for @{args.login}")
        for f in report.findings:
            print(f"  [{f.tier:>9}] {f.title}: {f.value:,.0f} {f.unit}")
    else:
        report = _load(args.assets)

    if args.cmd in ("render", "run"):
        for path in _render(report, args.assets):
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
