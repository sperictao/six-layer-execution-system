#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_task_dependency_graph.py"
TASK_DOC = WORKSPACE / "tasks" / "execution-system-decomposition-upgrade-tasks.md"


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

    with tempfile.TemporaryDirectory(prefix="task-dep-graph-") as tmpdir:
        tmp = Path(tmpdir)

        happy = tmp / "tasks-happy.md"
        happy.write_text(original, encoding="utf-8")
        expect_ok("happy-path", run_checker(happy))

        unknown_dep = tmp / "tasks-unknown-dep.md"
        unknown_dep.write_text(
            "# sample\n\n## PR queue\n\n#### Slice A1 - first\n- phase_id: `PH-1`\n- depends_on:\n  - `DX-Z.Z9`\n- parallel_safe:\n  - false\n- shared_write_targets:\n  - `docs/sample.md`\n- expected_artifacts:\n  - sample\n- integration_notes:\n  - sample\n- handoff_output:\n  - sample\n- rollback_strategy:\n  - revert sample\n",
            encoding="utf-8",
        )
        expect_fail(
            "unknown-dependency",
            run_checker(unknown_dep),
            "depends on unknown slice `Z9`",
        )

        cycle = tmp / "tasks-cycle.md"
        cycle.write_text(
            "# sample\n\n## PR queue\n\n#### Slice A1 - first\n- phase_id: `PH-1`\n- depends_on:\n  - `DX-A.B1`\n- parallel_safe:\n  - false\n- shared_write_targets:\n  - `docs/a.md`\n- expected_artifacts:\n  - a\n- integration_notes:\n  - a\n- handoff_output:\n  - a\n- rollback_strategy:\n  - revert a\n\n#### Slice B1 - second\n- phase_id: `PH-1`\n- depends_on:\n  - `DX-A.A1`\n- parallel_safe:\n  - false\n- shared_write_targets:\n  - `docs/b.md`\n- expected_artifacts:\n  - b\n- integration_notes:\n  - b\n- handoff_output:\n  - b\n- rollback_strategy:\n  - revert b\n",
            encoding="utf-8",
        )
        expect_fail(
            "dependency-cycle",
            run_checker(cycle),
            "dependency cycle `A1 -> B1 -> A1`",
        )

    print("TASK_DEPENDENCY_GRAPH_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
