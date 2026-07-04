"""The verdict meter — reception, measured.

Output is what we ship; the verdict is what the world does about it.
This module records the external signals (followers, stars across the
estate, traffic on the showcase repo) as a daily time series in
``assets/verdict.jsonl`` and renders a meter card with deltas, so
"changing the verdict" is a chart that either moves or doesn't.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .render import BG, BORDER, GOLD, MUTED, _STYLE, _shimmer

API = "https://api.github.com"


def _rest(path: str, token: str) -> Any:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Authorization": f"bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "laurea",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def collect_verdict(snapshot: dict[str, Any], repo: str, token: str, today: str) -> dict[str, Any]:
    """One day's reception entry. Traffic needs push access; degrade gracefully."""
    entry: dict[str, Any] = {
        "date": today,
        "followers": snapshot["followers"],
        "stars_estate": sum(r["stargazerCount"] for r in snapshot["repos"]),
    }
    try:
        entry["showcase_stars"] = _rest(f"/repos/{repo}", token)["stargazers_count"]
        views = _rest(f"/repos/{repo}/traffic/views", token)
        clones = _rest(f"/repos/{repo}/traffic/clones", token)
        entry["views_14d"] = views["count"]
        entry["unique_visitors_14d"] = views["uniques"]
        entry["clones_14d"] = clones["count"]
    except Exception:
        pass  # public-only token: the estate signals still record
    return entry


def append_entry(entry: dict[str, Any], jsonl: Path) -> list[dict[str, Any]]:
    """Append today's entry (idempotent per date); return full history."""
    history = load_history(jsonl)
    history = [e for e in history if e["date"] != entry["date"]] + [entry]
    history.sort(key=lambda e: e["date"])
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text("".join(json.dumps(e) + "\n" for e in history))
    return history


def load_history(jsonl: Path) -> list[dict[str, Any]]:
    if not jsonl.exists():
        return []
    return [json.loads(line) for line in jsonl.read_text().splitlines() if line.strip()]


def deltas(history: list[dict[str, Any]], key: str) -> tuple[float | None, float | None]:
    """(current, delta vs oldest recorded) for one signal."""
    series = [e[key] for e in history if key in e]
    if not series:
        return None, None
    return series[-1], (series[-1] - series[0]) if len(series) > 1 else None


_ROWS = (
    ("stars_estate", "stars across the estate"),
    ("followers", "followers"),
    ("showcase_stars", "showcase repo stars"),
    ("unique_visitors_14d", "unique visitors (14d)"),
)


def verdict_card(history: list[dict[str, Any]]) -> str:
    since = history[0]["date"] if history else "—"
    rows = []
    for i, (key, label) in enumerate(_ROWS):
        current, delta = deltas(history, key)
        if current is None:
            continue
        d = "baseline" if delta is None else (f"+{delta:,.0f}" if delta >= 0 else f"{delta:,.0f}")
        color = GOLD if delta and delta > 0 else MUTED
        rows.append(
            f'<g class="fade d{i + 1}" transform="translate(0,{96 + i * 30})">'
            f'<text class="t" x="32" y="0">{escape(label)}</text>'
            f'<text class="big" x="300" y="2" style="font-size:20px" text-anchor="end">{current:,.0f}</text>'
            f'<text class="tier" x="388" y="2" text-anchor="end" fill="{color}">{escape(d)}</text></g>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="230" viewBox="0 0 420 230" role="img" aria-label="Verdict meter — reception signals">
  {_STYLE}
  <defs>{_shimmer("V")}</defs>
  <rect width="419" height="229" x="0.5" y="0.5" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <text class="tier fade" fill="url(#shV)" x="32" y="38" style="font-size:15px">THE VERDICT METER</text>
  <text class="ev fade d1" x="32" y="58">reception, measured daily — output is claimed above; this is what the world did</text>
  {"".join(rows)}
  <text class="ev fade d4" x="32" y="216" fill="{MUTED}">tracking since {escape(since)} · a verdict is a chart, not a feeling</text>
</svg>
"""
