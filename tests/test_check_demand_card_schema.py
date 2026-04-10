#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE

CHECKER = WORKSPACE / "scripts" / "check_demand_card_schema.py"


def run_checker(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CHECKER), *(str(path) for path in paths)],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_ok(name: str, proc: subprocess.CompletedProcess[str], needle: str | None = None) -> None:
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass, got {output}")
    if needle and needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def expect_fail(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    output = proc.stdout + proc.stderr
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail")
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="demand-card-check-") as tmpdir:
        tmp = Path(tmpdir)

        empty_dir = tmp / "empty"
        empty_dir.mkdir()
        expect_ok("empty-dir", run_checker(empty_dir), "- scanned_files: 0")

        happy = tmp / "happy-demand.md"
        happy.write_text(
            "# sample demand intake\n\n"
            "- request: implement a generated backlog\n"
            "- task_type: `implementation`\n"
            "- desired_outcome: create aligned demand roadmap and tasks artifacts\n"
            "- scope:\n"
            "  - demands/sample-demand.md\n"
            "- constraints:\n"
            "  - keep ACTIVE as runtime truth\n"
            "- non_goals:\n"
            "  - do not rewrite unrelated activities\n"
            "- risk_level: `medium`\n"
            "- external_confirmation_required: `false`\n"
            "- dependency_graph:\n"
            "  - AA-A.A1 -> AA-A.B1 -> AA-A.C1\n"
            "- parallelizable_units:\n"
            "  - none\n"
            "- serial_units:\n"
            "  - AA-A.A1\n"
            "- expected_artifacts:\n"
            "  - demands/sample-demand.md\n"
            "- validation_plan:\n"
            "  - python3 scripts/run_execution_checks.py checks --timeout 60\n"
            "- closeout_condition:\n"
            "  - generated artifacts stay aligned\n",
            encoding="utf-8",
        )
        expect_ok("happy-path", run_checker(happy), "- scanned_files: 1")

        missing_task_type = tmp / "missing-task-type.md"
        missing_task_type.write_text(
            "# sample demand intake\n\n"
            "- request: implement a generated backlog\n"
            "- desired_outcome: create aligned demand roadmap and tasks artifacts\n"
            "- scope:\n"
            "  - demands/sample-demand.md\n"
            "- constraints:\n"
            "  - keep ACTIVE as runtime truth\n"
            "- non_goals:\n"
            "  - do not rewrite unrelated activities\n"
            "- risk_level: `medium`\n"
            "- external_confirmation_required: `false`\n"
            "- dependency_graph:\n"
            "  - AA-A.A1 -> AA-A.B1 -> AA-A.C1\n"
            "- parallelizable_units:\n"
            "  - none\n"
            "- serial_units:\n"
            "  - AA-A.A1\n"
            "- expected_artifacts:\n"
            "  - demands/sample-demand.md\n"
            "- validation_plan:\n"
            "  - python3 scripts/run_execution_checks.py checks --timeout 60\n"
            "- closeout_condition:\n"
            "  - generated artifacts stay aligned\n",
            encoding="utf-8",
        )
        expect_fail("missing-task-type", run_checker(missing_task_type), "missing `task_type`")

        invalid_risk = tmp / "invalid-risk.md"
        invalid_risk.write_text(
            happy.read_text(encoding="utf-8").replace("- risk_level: `medium`", "- risk_level: `critical`"),
            encoding="utf-8",
        )
        expect_fail("invalid-risk", run_checker(invalid_risk), "invalid `risk_level` `critical`")

    print("DEMAND_CARD_SCHEMA_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
