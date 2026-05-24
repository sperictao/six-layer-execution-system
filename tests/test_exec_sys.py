#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from execution_system_paths import WORKSPACE
from test_workspace_clone import cloned_workspace

EXEC_SYS = WORKSPACE / "scripts" / "exec_sys.py"


def activate_simple_fixture(workspace: Path) -> None:
    activity_id = "simple-ledger-docs"
    activity_dir = workspace / "activities" / activity_id
    activity_dir.mkdir(parents=True, exist_ok=True)
    (activity_dir / "card.md").write_text(
        """### Activity: simple-ledger-docs
- activity_id: `simple-ledger-docs`
- title: `Simple ledger docs`
- type: `simple`
- status: `ready`
- priority: `P2`
- autopilot: `true`
- focus_rank: `1`
- goal: `exercise exec_sys status`
- done_definition: `status command reports focus`
- next_step:
  - run status
- validation:
  - inspect output
""",
        encoding="utf-8",
    )

    active = workspace / "ACTIVE.md"
    active_text = active.read_text(encoding="utf-8")
    active_text = active_text.replace(
        "- current_focus_activity_id: `none`",
        "- current_focus_activity_id: `simple-ledger-docs`",
        1,
    )
    row = "| simple-ledger-docs | simple | ready | P2 | activities/simple-ledger-docs/ |\n"
    marker = "|------------|------|--------|----------|------|\n"
    active_text = active_text.replace(marker, marker + row, 1)
    active.write_text(active_text, encoding="utf-8")


def main() -> int:
    with cloned_workspace() as workspace:
        activate_simple_fixture(workspace)

        env = os.environ.copy()
        env.pop("SIX_LAYER_WORKSPACE", None)
        env["SIX_LAYER_REPO_ROOT"] = str(workspace)

        proc = subprocess.run(
            ["python3", str(EXEC_SYS), "status"],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

        output = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise AssertionError(f"exec_sys status should succeed with SIX_LAYER_REPO_ROOT fallback\n{output}")
        if "Current Focus Activity: simple-ledger-docs" not in output:
            raise AssertionError(
                "exec_sys should honor SIX_LAYER_REPO_ROOT when SIX_LAYER_WORKSPACE is unset\n"
                f"{output}"
            )

    print("EXEC_SYS_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
