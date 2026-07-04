"""Animated SVG laurels + the generated SUPERLATIVES report.

Pure string templating over stdlib — the SVGs embed SMIL/CSS animation
(gradient shimmer, staged fade-in), which GitHub's image proxy renders
inside READMEs. Every card carries its evidence line so a claim never
travels without its receipt.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .baselines import TIER_TOP_01, TIER_TOP_1, TIER_TOP_5, odds_for
from .models import Finding, Report

GOLD = "#e3b341"
GOLD_DIM = "#9e7b2a"
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
FG = "#e6edf3"
MUTED = "#8b949e"

_TIER_COLOR = {
    TIER_TOP_01: "#ffd700",
    TIER_TOP_1: GOLD,
    TIER_TOP_5: "#c9a227",
}

_STYLE = f"""
  <style>
    .t {{ font: 600 15px 'Segoe UI', Helvetica, Arial, sans-serif; fill: {FG}; }}
    .big {{ font: 700 34px 'Segoe UI', Helvetica, Arial, sans-serif; fill: {GOLD}; }}
    .tier {{ font: 700 13px 'Segoe UI', Helvetica, Arial, sans-serif; letter-spacing: 1px; }}
    .ev {{ font: 400 12px 'Segoe UI', Helvetica, Arial, sans-serif; fill: {MUTED}; }}
    .fade {{ opacity: 0; animation: fadein 0.9s ease-out forwards; }}
    .d1 {{ animation-delay: 0.15s; }} .d2 {{ animation-delay: 0.3s; }}
    .d3 {{ animation-delay: 0.45s; }} .d4 {{ animation-delay: 0.6s; }}
    @keyframes fadein {{ to {{ opacity: 1; }} }}
  </style>
"""


def _shimmer(uid: str) -> str:
    """A slowly sweeping gold gradient — the living-laurel effect."""
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
    """Two mirrored laurel branches drawn as arced fronds."""
    fronds = "".join(
        f'<ellipse cx="0" cy="{-8 - i * 7}" rx="6" ry="2.6" '
        f'transform="rotate({-24 - i * 5} 0 {-8 - i * 7})" fill="url(#shL)"/>'
        for i in range(5)
    )
    branch = f'<path d="M0,4 Q-3,-18 2,-42" stroke="url(#shL)" stroke-width="2" fill="none"/>{fronds}'
    return (
        f'<g transform="translate({x},{y}) scale({scale})">'
        f'<g transform="translate(-16,0)">{branch}</g>'
        f'<g transform="translate(16,0) scale(-1,1)">{branch}</g>'
        f"</g>"
    )


def _fmt(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.1f}"


def _wrap(text: str, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return lines


def hero_card(report: Report) -> str:
    composite = report.by_axis("composite_python_full_stack")
    headline = (
        "TOP 1% PYTHON FULL-STACK ENGINEER"
        if composite
        else "ENGINEERING OUTPUT — MEASURED"
    )
    c = report.snapshot["contributions"]
    repos = len([r for r in report.snapshot["repos"] if not r["isFork"]])
    stats = (
        (f"{c['total']:,}", "contributions / yr"),
        (f"{repos:,}", "repos owned"),
        (f"{c['pull_requests']:,}", "PRs / yr"),
        (f"{len(report.snapshot['orgs'])}", "orgs operated"),
    )
    cols = "".join(
        f"""
  <g class="fade d{i + 1}" transform="translate({70 + i * 180}, 150)">
    <text class="big" text-anchor="middle" x="60">{escape(v)}</text>
    <text class="ev" text-anchor="middle" x="60" y="24">{escape(label)}</text>
  </g>"""
        for i, (v, label) in enumerate(stats)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240" viewBox="0 0 800 240" role="img" aria-label="{escape(headline)}">
  {_STYLE}
  <defs>{_shimmer("H")}{_shimmer("L")}</defs>
  <rect width="799" height="239" x="0.5" y="0.5" rx="12" fill="{BG}" stroke="{BORDER}"/>
  {_laurel(400, 78, 1.1)}
  <text class="tier fade" fill="url(#shH)" text-anchor="middle" x="400" y="96" style="font-size:20px">{escape(headline)}</text>
  <text class="ev fade d1" text-anchor="middle" x="400" y="118">computed, not claimed — every floor is odds you can read: top 1% means at least 1 in 100, top 0.1% at least 1 in 1,000</text>
  {cols}
  <text class="ev fade d4" text-anchor="middle" x="400" y="222">LAVREA · the laurels are computed · github.com/{escape(report.login)}/laurea</text>
</svg>
"""


def axis_card(finding: Finding) -> str:
    color = _TIER_COLOR.get(finding.tier, MUTED)
    ev_lines = _wrap(finding.evidence, 58)[:3]
    ev = "".join(
        f'<text class="ev fade d{i + 2}" x="24" y="{104 + i * 16}">{escape(line)}</text>'
        for i, line in enumerate(ev_lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="170" viewBox="0 0 420 170" role="img" aria-label="{escape(finding.title)}: {escape(finding.tier)}">
  {_STYLE}
  <defs>{_shimmer("L")}</defs>
  <rect width="419" height="169" x="0.5" y="0.5" rx="10" fill="{PANEL}" stroke="{BORDER}"/>
  <text class="t fade" x="24" y="34">{escape(finding.title)}</text>
  <text class="tier fade d1" x="396" y="34" text-anchor="end" fill="{color}">{escape(finding.tier.upper())}</text>
  {f'<text class="ev fade d2" x="396" y="50" text-anchor="end">{escape(odds)}</text>' if (odds := odds_for(finding.tier)) else ""}
  <text class="big fade d1" x="24" y="76">{escape(_fmt(finding.value))}</text>
  <text class="ev fade d2" x="{30 + 21 * len(_fmt(finding.value))}" y="76">{escape(finding.unit)}</text>
  {ev}
</svg>
"""


def superlatives_md(report: Report) -> str:
    lines = [
        "# SUPERLATIVES",
        "",
        f"*Generated {report.generated_at} for "
        f"[@{report.login}](https://github.com/{report.login}). "
        "Every claim below is recomputed from the live GitHub API; "
        "every percentile is a conservative floor with a cited baseline "
        "(see [METHODOLOGY.md](METHODOLOGY.md)).*",
        "",
    ]
    for f in report.findings:
        odds = odds_for(f.tier)
        heading = f"## {f.title} — **{f.tier}**" + (f" *({odds})*" if odds else "")
        lines += [
            heading,
            "",
            f"**Measured:** {f.value:,.0f} {f.unit}",
            "",
            f"{f.evidence}.",
            "",
        ]
        if f.analysis:
            lines += [f"**What this means:** {f.analysis}", ""]
        lines += [f"*Baseline: {f.source}.*", ""]
    return "\n".join(lines)


def render_all(report: Report) -> dict[str, str]:
    """Returns {relative_path: content} for everything to write to assets/."""
    out = {"cards/hero.svg": hero_card(report)}
    for f in report.findings:
        if f.axis == "composite_python_full_stack":
            continue  # the hero card carries the composite
        out[f"cards/{f.axis}.svg"] = axis_card(f)
    out["SUPERLATIVES.md"] = superlatives_md(report)
    return out
