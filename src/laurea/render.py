"""Animated SVG cards and the generated bounded activity report."""

from __future__ import annotations

from xml.sax.saxutils import escape

from .baselines import STATUS_DERIVED, STATUS_MEASURED
from .models import Finding, Report

NOT_MEASURED = (
    "individual authorship or responsibility for organization repositories",
    "code quality, correctness, maintainability, or security",
    "whether pull requests were reviewed, mergeable, or merged",
    "system reliability in production",
    "product adoption, user satisfaction, or business impact",
    "professional experience or engineering judgment",
)
PUBLIC_LIMITATION = (
    "GitHub activity does not establish authorship, quality, reliability, adoption, or impact."
)

GOLD = "#e3b341"
GOLD_DIM = "#9e7b2a"
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
FG = "#e6edf3"
MUTED = "#8b949e"

_STATUS_COLOR = {STATUS_MEASURED: GOLD, STATUS_DERIVED: MUTED}

_STYLE = f"""
  <style>
    .t {{ font: 600 15px 'Segoe UI', Helvetica, Arial, sans-serif; fill: {FG}; }}
    .big {{ font: 700 34px 'Segoe UI', Helvetica, Arial, sans-serif; fill: {GOLD}; }}
    .status {{ font: 700 13px 'Segoe UI', Helvetica, Arial, sans-serif; letter-spacing: 1px; }}
    .ev {{ font: 400 12px 'Segoe UI', Helvetica, Arial, sans-serif; fill: {MUTED}; }}
    .fade {{ opacity: 0; animation: fadein 0.9s ease-out forwards; }}
    .d1 {{ animation-delay: 0.15s; }} .d2 {{ animation-delay: 0.3s; }}
    .d3 {{ animation-delay: 0.45s; }} .d4 {{ animation-delay: 0.6s; }}
    @keyframes fadein {{ to {{ opacity: 1; }} }}
  </style>
"""


def _shimmer(uid: str) -> str:
    """Return the shared slow gold gradient."""
    return f"""
  <linearGradient id="sh{uid}" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{GOLD_DIM}"/>
    <stop offset="50%" stop-color="{GOLD}">
      <animate attributeName="offset" values="0.2;0.8;0.2" dur="6s" repeatCount="indefinite"/>
    </stop>
    <stop offset="100%" stop-color="{GOLD_DIM}"/>
  </linearGradient>
"""


def _laurel(x: int, y: int, scale: float = 1.0) -> str:
    """Return two mirrored decorative laurel branches."""
    fronds = "".join(
        f'<ellipse cx="0" cy="{-8 - index * 7}" rx="6" ry="2.6" '
        f'transform="rotate({-24 - index * 5} 0 {-8 - index * 7})" fill="url(#shL)"/>'
        for index in range(5)
    )
    branch = f'<path d="M0,4 Q-3,-18 2,-42" stroke="url(#shL)" stroke-width="2" fill="none"/>{fronds}'
    return (
        f'<g transform="translate({x},{y}) scale({scale})">'
        f'<g transform="translate(-16,0)">{branch}</g>'
        f'<g transform="translate(16,0) scale(-1,1)">{branch}</g>'
        "</g>"
    )


def _fmt(value: float) -> str:
    return f"{int(value):,}" if value == int(value) else f"{value:,.1f}"


def _wrap(text: str, width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and len(candidate) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def _tspans(lines: list[str], x: int, line_height: int = 14) -> str:
    return "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else line_height}">{escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )


def hero_card(report: Report) -> str:
    """Render a generic profile card without population-ranking claims."""
    contributions = report.snapshot["contributions"]
    repositories = len([repo for repo in report.snapshot["repos"] if repo["isFork"] is False])
    stats = (
        (f"{contributions['total']:,}", ["contribution events", "trailing 12 months"]),
        (f"{repositories:,}", ["non-fork repositories", "visible corpus"]),
        (f"{contributions['pull_requests']:,}", ["pull requests opened", "trailing 12 months"]),
        (f"{len(report.snapshot['orgs'])}", ["organization memberships", "queried"]),
    )
    columns = "".join(
        f"""
  <g class="fade d{index + 1}" transform="translate({70 + index * 180}, 160)">
    <text class="big" text-anchor="middle" x="60">{escape(value)}</text>
    <text class="ev" text-anchor="middle" x="60" y="24">{_tspans(labels, 60)}</text>
  </g>"""
        for index, (value, labels) in enumerate(stats)
    )
    limitation = _tspans(_wrap(PUBLIC_LIMITATION, 86), 400, 15)
    source = report.source_repository if report.source_repository != "unknown" else "source repository unavailable"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="270" viewBox="0 0 800 270" role="img" aria-label="Measured GitHub activity profile">
  {_STYLE}
  <defs>{_shimmer("H")}{_shimmer("L")}</defs>
  <rect width="799" height="269" x="0.5" y="0.5" rx="12" fill="{BG}" stroke="{BORDER}"/>
  {_laurel(400, 76, 1.1)}
  <text class="status fade" fill="url(#shH)" text-anchor="middle" x="400" y="96" style="font-size:20px">MEASURED GITHUB ACTIVITY PROFILE</text>
  <text class="ev fade d1" text-anchor="middle" x="400" y="119">{limitation}</text>
  {columns}
  <text class="ev fade d4" text-anchor="middle" x="400" y="252">LAVREA · generated for @{escape(report.login)} · {escape(source)}</text>
</svg>
"""


def axis_card(finding: Finding) -> str:
    """Render one measured or derived observation with bounded copy."""
    color = _STATUS_COLOR[finding.status]
    evidence_lines = _wrap(finding.evidence, 58)[:3]
    evidence = "".join(
        f'<text class="ev fade d{index + 2}" x="24" y="{104 + index * 16}">{escape(line)}</text>'
        for index, line in enumerate(evidence_lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="170" viewBox="0 0 420 170" role="img" aria-label="{escape(finding.title)}: {escape(finding.status)}">
  {_STYLE}
  <defs>{_shimmer("L")}</defs>
  <rect width="419" height="169" x="0.5" y="0.5" rx="10" fill="{PANEL}" stroke="{BORDER}"/>
  <text class="t fade" x="24" y="34">{escape(finding.title)}</text>
  <text class="status fade d1" x="396" y="34" text-anchor="end" fill="{color}">{escape(finding.status.upper())}</text>
  <text class="big fade d1" x="24" y="76">{escape(_fmt(finding.value))}</text>
  <text class="ev fade d2" x="{30 + 21 * len(_fmt(finding.value))}" y="76">{escape(finding.unit)}</text>
  {evidence}
</svg>
"""


def profile_md(report: Report) -> str:
    """Render the full bounded report without heuristic rankings."""
    lines = [
        "# MEASURED PROFILE",
        "",
        f"*Generated {report.generated_at} for [@{report.login}](https://github.com/{report.login}). "
        "Counts come from the GitHub API; derived observations name their transformation. "
        "No percentile ranking is published because this repository does not carry a validated "
        "population distribution.*",
        "",
    ]
    for finding in report.findings:
        evidence = finding.evidence.rstrip(".")
        lines += [
            f"## {finding.title} — **{finding.status}**",
            "",
            f"**Observed:** {finding.value:,.0f} {finding.unit}",
            "",
            f"{evidence}.",
            "",
            f"**Definition:** {finding.source}.",
            "",
            f"**Boundary:** {finding.analysis}",
            "",
        ]
    lines += [
        "## What these numbers do not establish",
        "",
        "LAVREA reports an API-visible activity and repository corpus. It does not establish:",
        "",
    ]
    lines += [f"- {item}" for item in NOT_MEASURED]
    lines += ["", PUBLIC_LIMITATION, ""]
    return "\n".join(lines)


def render_all(report: Report) -> dict[str, str]:
    """Return every generated relative path and its content."""
    output = {"cards/hero.svg": hero_card(report)}
    for finding in report.findings:
        output[f"cards/{finding.axis}.svg"] = axis_card(finding)
    output["PROFILE.md"] = profile_md(report)
    return output
