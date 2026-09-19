"""Exercise the actual workflow's entry-only admission command."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import pytest

from laurea.arena import write_entry


@pytest.mark.parametrize("malformed", [False, True])
def test_workflow_checks_entry_inventory_without_replacing_table(tmp_path, malformed):
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/validate.yml").read_text()
    block = workflow.split("      - name: Validate arena entry inventory\n", 1)[1]
    command = textwrap.dedent(block.split("        run: |\n", 1)[1].split("      - ", 1)[0])
    arena = tmp_path / "arena"
    arena.mkdir()
    shutil.copy(root / "arena/baseline.json", arena / "baseline.json")
    write_entry(arena / "entries", issue=123,
                row=dict(login="fixture", contributions=1, prs=2, repos=3,
                         languages=1, measured_axes=4, verified="2026-09-18"),
                observed_at="2026-09-18T12:00:00+00:00")
    if malformed:
        (arena / "entries/123.json").write_text("{}")
    table = tmp_path / "LEADERBOARD.md"
    table.write_text("existing table awaiting separate refresh\n")
    env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])
    result = subprocess.run(["bash", "-euo", "pipefail", "-c", command], cwd=tmp_path,
                            env=env, capture_output=True, text=True)
    assert (result.returncode != 0) is malformed, result.stderr
    assert table.read_text() == "existing table awaiting separate refresh\n"
