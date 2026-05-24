#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_parallel_safety.py"
HAPPY_TASKS = """# sample

## PR queue

#### Slice A1 - parallel
- phase_id: `PH-1`
- depends_on:
  - none
- parallel_safe:
  - true
- shared_write_targets:
  - none
- expected_artifacts:
  - a
- integration_notes:
  - a
- rollback_strategy:
  - revert a

#### Slice B1 - serial
- phase_id: `PH-1`
- depends_on:
  - `DX-A.A1`
- parallel_safe:
  - false
- shared_write_targets:
  - `docs/b.md`
- expected_artifacts:
  - b
- integration_notes:
  - b
- rollback_strategy:
  - revert b
"""


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
    with tempfile.TemporaryDirectory(prefix="parallel-safety-") as tmpdir:
        tmp = Path(tmpdir)

        happy = tmp / "tasks-happy.md"
        happy.write_text(HAPPY_TASKS, encoding="utf-8")
        expect_ok("happy-path", run_checker(happy))

        conflict = tmp / "tasks-conflict.md"
        conflict.write_text(
            "# sample\n\n## PR queue\n\n#### Slice A1 - sample\n- phase_id: `PH-1`\n- depends_on:\n  - none\n- parallel_safe:\n  - true\n- shared_write_targets:\n  - `docs/sample.md`\n- expected_artifacts:\n  - sample\n- integration_notes:\n  - sample\n- handoff_output:\n  - sample\n- rollback_strategy:\n  - revert sample\n",
            encoding="utf-8",
        )
        expect_fail(
            "parallel-safe-conflict",
            run_checker(conflict),
            "`parallel_safe: true` conflicts with non-empty `shared_write_targets`",
        )

        unexplained_serial = tmp / "tasks-unexplained-serial.md"
        unexplained_serial.write_text(
            "# sample\n\n## PR queue\n\n#### Slice A1 - sample\n- phase_id: `PH-1`\n- depends_on:\n  - none\n- parallel_safe:\n  - false\n- shared_write_targets:\n- expected_artifacts:\n  - sample\n- integration_notes:\n  - sample\n- handoff_output:\n  - sample\n- rollback_strategy:\n  - revert sample\n",
            encoding="utf-8",
        )
        expect_fail(
            "unexplained-serial",
            run_checker(unexplained_serial),
            "missing `shared_write_targets`",
        )

    print("PARALLEL_SAFETY_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
