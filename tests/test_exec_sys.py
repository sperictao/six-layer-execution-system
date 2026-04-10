#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess

from execution_system_paths import WORKSPACE
from test_workspace_clone import cloned_workspace

EXEC_SYS = WORKSPACE / "scripts" / "exec_sys.py"


def main() -> int:
    with cloned_workspace() as workspace:
        active = workspace / "ACTIVE.md"
        active_text = active.read_text(encoding="utf-8")
        active.write_text(
            active_text.replace(
                "- current_focus_activity_id: `waiting-ledger-review`",
                "- current_focus_activity_id: `simple-ledger-docs`",
                1,
            ),
            encoding="utf-8",
        )

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
