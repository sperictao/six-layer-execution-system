#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_task_slice_schema.py"
TASK_DOC = WORKSPACE / "tasks" / "one-publish-refactor-tasks.md"


def run_checker(task_doc: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CHECKER), str(task_doc)],
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
    original = TASK_DOC.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="task-slice-check-") as tmpdir:
        tmp = Path(tmpdir)

        happy = tmp / "tasks-happy.md"
        happy.write_text(original, encoding="utf-8")
        expect_ok("happy-path", run_checker(happy))

        legacy_only = tmp / "tasks-legacy-only.md"
        legacy_only.write_text(
            "# sample\n\n## PR queue\n\n#### Task 1 - legacy sample\n- objective:\n  - legacy block\n",
            encoding="utf-8",
        )
        expect_ok("legacy-heading-out-of-scope", run_checker(legacy_only))

        missing_rollback = tmp / "tasks-missing-rollback.md"
        missing_rollback.write_text(
            "# sample\n\n## PR queue\n\n#### Slice P2 - first frontend shell-collapse cut\n- phase_id: `PH-5`\n- goal:\n  - shell collapse\n",
            encoding="utf-8",
        )
        expect_fail(
            "missing-rollback-strategy",
            run_checker(missing_rollback),
            "Slice P2 - first frontend shell-collapse cut: missing `rollback_strategy`",
        )

    print("TASK_SLICE_SCHEMA_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
