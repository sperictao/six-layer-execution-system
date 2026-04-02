#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from test_workspace_clone import cloned_workspace, workspace_env

TARGET_LINE = "- heartbeat 与人工触发必须遵守同一套恢复规则；不得因为是 heartbeat 就跳过 `ACTIVE.md` / focus activity / roadmap/tasks / repo fact check 这些步骤\n"


def run(script: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", str(script)], text=True, capture_output=True, check=False, env=env)


def expect_contains(output: str, needle: str) -> None:
    if needle not in output:
        raise AssertionError(f"missing expected text: {needle}\n{output}")


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        runner = workspace / "scripts" / "run_execution_system_checks.py"
        governance_script = workspace / "scripts" / "check_execution_system_governance_consistency.py"
        skill = workspace / "skills" / "six-layer-execution-system" / "SKILL.md"
        original = skill.read_text(encoding="utf-8")
        if TARGET_LINE not in original:
            raise AssertionError("target skill line missing before test")

        broken = original.replace(TARGET_LINE, "", 1)
        skill.write_text(broken, encoding="utf-8")

        governance = run(governance_script, env)
        governance_output = governance.stdout + governance.stderr
        if governance.returncode == 0:
            raise AssertionError("governance checker should fail when skill recovery rule drifts")
        expect_contains(governance_output, "EXECUTION_SYSTEM_GOVERNANCE_CONSISTENCY_FAILED")
        expect_contains(
            governance_output,
            "skill: missing `heartbeat 与人工触发必须遵守同一套恢复规则`",
        )

        runner_proc = run(runner, env)
        runner_output = runner_proc.stdout + runner_proc.stderr
        if runner_proc.returncode == 0:
            raise AssertionError("runner should fail when governance checker fails")
        expect_contains(runner_output, "EXECUTION_SYSTEM_CHECKS_FAILED")
        expect_contains(
            runner_output,
            "- first_failing_command: python3 ",
        )
        expect_contains(
            runner_output,
            "workspace/scripts/check_execution_system_governance_consistency.py",
        )
        expect_contains(
            runner_output,
            "- recovery_hint: inspect spec/skill alignment and repair the drifted recovery rule",
        )

        skill.write_text(original, encoding="utf-8")
        restored = run(governance_script, env)
        restored_output = restored.stdout + restored.stderr
        if restored.returncode != 0:
            raise AssertionError(f"governance checker should recover after restore\n{restored_output}")
        expect_contains(restored_output, "EXECUTION_SYSTEM_GOVERNANCE_CONSISTENCY_OK")

    print("EXECUTION_WORKFLOW_GOVERNANCE_DRIFT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
