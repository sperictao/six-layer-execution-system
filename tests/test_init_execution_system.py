#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE


EXEC_SYS = WORKSPACE / "scripts" / "exec_sys.py"


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(args, text=True, capture_output=True, check=False, env=merged_env)


def workspace_env(workspace: Path) -> dict[str, str]:
    return {
        "SIX_LAYER_REPO_ROOT": str(workspace),
        "SIX_LAYER_WORKSPACE": str(workspace),
        "SIX_LAYER_STATE_ROOT": str(workspace / "local-state"),
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="six-layer-init-") as tmpdir:
        root = Path(tmpdir)
        target = root / "new-root"

        proc = run_command(["python3", str(EXEC_SYS), "init", "--target", str(target)])
        output = proc.stdout + proc.stderr
        expect(proc.returncode == 0, output)
        expect("EXECUTION_SYSTEM_INIT_OK" in output, output)
        expect((target / "ACTIVE.md").exists(), "init should create ACTIVE.md")
        expect((target / "scripts" / "exec_sys.py").exists(), "init should copy scripts")
        expect(not (target / "SKILL.md").exists(), "init should not create a root-level skill shim")
        expect(
            (target / "skills" / "six-layer-execution-system" / "SKILL.md").exists(),
            "init should copy the canonical skill",
        )
        expect((target / "local-state").is_dir(), "init should create local-state")
        expect(
            "- current_focus_activity_id: `none`" in (target / "ACTIVE.md").read_text(encoding="utf-8"),
            "fresh ACTIVE.md should start idle",
        )

        inspect_proc = run_command(
            ["python3", str(target / "scripts" / "inspect_execution_system.py"), "--format", "json"],
            env=workspace_env(target),
        )
        inspect_output = inspect_proc.stdout + inspect_proc.stderr
        expect(inspect_proc.returncode == 0, inspect_output)
        snapshot = json.loads(inspect_proc.stdout)
        expect(snapshot["plugin"]["root"] == str(target.resolve()), inspect_proc.stdout)
        expect(snapshot["ledger"]["current_focus_activity_id"] == "none", inspect_proc.stdout)

        active_proc = run_command(
            ["python3", str(target / "scripts" / "run_execution_checks.py"), "active", "--timeout", "60"],
            env=workspace_env(target),
        )
        active_output = active_proc.stdout + active_proc.stderr
        expect(active_proc.returncode == 0, active_output)
        expect("CONSISTENCY_CHECK_OK" in active_output, active_output)

        second_proc = run_command(["python3", str(EXEC_SYS), "init", "--target", str(target)])
        second_output = second_proc.stdout + second_proc.stderr
        expect(second_proc.returncode == 0, second_output)
        expect("- overwritten: 0" in second_output, second_output)

        conflict_target = root / "conflict-root"
        conflict_target.mkdir()
        (conflict_target / "README.md").write_text("custom project readme\n", encoding="utf-8")
        conflict_proc = run_command(["python3", str(EXEC_SYS), "init", "--target", str(conflict_target)])
        conflict_output = conflict_proc.stdout + conflict_proc.stderr
        expect(conflict_proc.returncode == 1, conflict_output)
        expect("EXECUTION_SYSTEM_INIT_CONFLICT" in conflict_output, conflict_output)
        expect("README.md exists and differs" in conflict_output, conflict_output)
        expect(not (conflict_target / "ACTIVE.md").exists(), "conflict preflight should not partially initialize")

    print("INIT_EXECUTION_SYSTEM_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
