#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from execution_system_paths import WORKSPACE
from test_workspace_clone import cloned_workspace, init_git_repo, workspace_env

CHECKER = WORKSPACE / "scripts" / "check_generated_decomposition_consistency.py"
SOURCE_DEMAND = "demands/2026-04-10-auto-decompose-natural-language-demand.md"
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

        roadmap = workspace / "roadmaps" / "auto-decompose-natural-language-demand-roadmap.md"
        roadmap_text = roadmap.read_text(encoding="utf-8")
        roadmap.write_text(
            roadmap_text.replace(
                f"- `{SOURCE_DEMAND}`",
                "- `demands/drifted-demand.md`",
                1,
            ),
            encoding="utf-8",
        )
        expect_fail(
            "source-demand-drift",
            run_checker(workspace, env),
            "roadmap Source demand `demands/drifted-demand.md` does not match",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        active = workspace / "ACTIVE.md"
        active_text = active.read_text(encoding="utf-8")
        target = (
            f"- activity_id: `{ACTIVITY_ID}`\n"
            "- title: `auto decompose Auto decompose natural-language demand`\n"
            "- type: `roadmap`\n"
            "- owner: `Codex`\n"
            "- status: `blocked`\n"
            "- priority: `P1`\n"
            "- autopilot: `false`\n"
        )
        replacement = target.replace("- autopilot: `false`", "- autopilot: `true`")
        active.write_text(active_text.replace(target, replacement, 1), encoding="utf-8")
        expect_fail(
            "high-risk-autopilot-drift",
            run_checker(workspace, env),
            "high-risk or confirmation-required generated activity must keep `autopilot: false`",
        )

    print("GENERATED_DECOMPOSITION_CONSISTENCY_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
