#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_task_slice_schema.py"


def run_checker(tasks_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CHECKER), str(tasks_dir)],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_ok(name: str, proc: subprocess.CompletedProcess[str]) -> None:
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass, got {proc.stdout}{proc.stderr}")


def expect_fail(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail")
    output = proc.stdout + proc.stderr
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="task-slice-check-") as tmpdir:
        tmp = Path(tmpdir)

        # v3: create a tasks directory with valid slice files
        happy_dir = tmp / "tasks-happy"
        happy_dir.mkdir()
        (happy_dir / "B1.md").write_text(
            "# Slice B1 — normalize execution-system semantic tests\n"
            "- activity_id: `execution-system-testing`\n"
            "- phase_id: `PH-2`\n"
            "- status: `ready`\n"
            "- goal:\n"
            "  - normalize semantic smoke ownership\n"
            "- scope:\n"
            "  - test files\n"
            "- rollback_strategy:\n"
            "  - `git revert`\n"
            "- risk: low\n",
            encoding="utf-8",
        )
        expect_ok("happy-path", run_checker(happy_dir))

        # Test missing rollback_strategy
        missing_dir = tmp / "tasks-missing"
        missing_dir.mkdir()
        (missing_dir / "B1.md").write_text(
            "# Slice B1 — normalize execution-system semantic tests\n"
            "- activity_id: `execution-system-testing`\n"
            "- phase_id: `PH-2`\n"
            "- status: `ready`\n"
            "- goal:\n"
            "  - normalize semantic smoke ownership\n",
            encoding="utf-8",
        )
        expect_fail(
            "missing-rollback-strategy",
            run_checker(missing_dir),
            "missing `rollback_strategy`",
        )

        # Test in_progress without actual_execution_plan
        inprog_dir = tmp / "tasks-inprog"
        inprog_dir.mkdir()
        (inprog_dir / "B1.md").write_text(
            "# Slice B1 — test\n"
            "- activity_id: `test`\n"
            "- phase_id: `PH-1`\n"
            "- status: `in_progress`\n"
            "- rollback_strategy:\n"
            "  - `git revert`\n"
            "- risk: low\n",
            encoding="utf-8",
        )
        expect_fail(
            "in-progress-no-plan",
            run_checker(inprog_dir),
            "in_progress but missing `actual_execution_plan`",
        )

    print("TASK_SLICE_SCHEMA_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
