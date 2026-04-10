#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess

from execution_system_paths import WORKSPACE
from test_workspace_clone import cloned_workspace

INSPECT = WORKSPACE / "scripts" / "inspect_execution_system.py"


def main() -> int:
    with cloned_workspace() as workspace:
        env = os.environ.copy()
        env.pop("SIX_LAYER_WORKSPACE", None)
        env["SIX_LAYER_REPO_ROOT"] = str(workspace)

        proc = subprocess.run(
            ["python3", str(INSPECT), "--format", "json"],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

        output = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise AssertionError(f"inspect_execution_system should succeed with SIX_LAYER_REPO_ROOT fallback\n{output}")

        try:
            snapshot = json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            raise AssertionError(f"inspect_execution_system should emit valid JSON\n{output}") from error

        expected_root = str(workspace.resolve())
        if snapshot.get("plugin", {}).get("root") != expected_root:
            raise AssertionError(
                "inspect_execution_system should honor SIX_LAYER_REPO_ROOT when SIX_LAYER_WORKSPACE is unset\n"
                f"expected={expected_root}\nactual={snapshot.get('plugin', {}).get('root')}\n{output}"
            )
        if snapshot.get("plugin", {}).get("exists") is not True:
            raise AssertionError(f"fallback workspace should exist\n{output}")

    print("INSPECT_EXECUTION_SYSTEM_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
