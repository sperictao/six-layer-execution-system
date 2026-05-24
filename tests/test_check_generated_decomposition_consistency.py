#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from execution_system_paths import WORKSPACE
from test_workspace_clone import cloned_workspace, init_git_repo, workspace_env

CHECKER = WORKSPACE / "scripts" / "check_generated_decomposition_consistency.py"
SOURCE_DEMAND = "activities/auto-auto-decompose-natural-language-demand/0-demand.md"
ACTIVITY_ID = "auto-auto-decompose-natural-language-demand"


def run_checker(workspace, env):
    return subprocess.run(
        ["python3", str(workspace / "scripts" / "check_generated_decomposition_consistency.py")],
        text=True,
        capture_output=True,
        check=False,
        env=env,
        cwd=workspace,
    )


def expect_ok(name: str, proc, needle: str) -> None:
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass\n{output}")
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def expect_fail(name: str, proc, needle: str) -> None:
    output = proc.stdout + proc.stderr
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail\n{output}")
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        expect_ok(
            "happy-path",
            run_checker(workspace, env),
            "GENERATED_DECOMPOSITION_CONSISTENCY_CHECK_OK",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        # v3: update the activity card instead of ACTIVE.md
        roadmap = workspace / "activities" / "auto-auto-decompose-natural-language-demand" / "2-roadmap.md"
        roadmap_text = roadmap.read_text(encoding="utf-8")
        roadmap.write_text(
            roadmap_text.replace(
                f"- `{SOURCE_DEMAND}`",
                "- `activities/auto-auto-decompose-natural-language-demand/drifted-demand.md`",
                1,
            ),
            encoding="utf-8",
        )
        expect_fail(
            "source-demand-drift",
            run_checker(workspace, env),
            "Source demand",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        # v3: update card.md instead of ACTIVE.md
        card = workspace / "activities" / ACTIVITY_ID / "card.md"
        card_text = card.read_text(encoding="utf-8")
        target = "- autopilot: `false`"
        replacement = "- autopilot: `true`"
        card.write_text(card_text.replace(target, replacement, 1), encoding="utf-8")
        expect_fail(
            "high-risk-autopilot-drift",
            run_checker(workspace, env),
            "autopilot",
        )

    print("GENERATED_DECOMPOSITION_CONSISTENCY_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
