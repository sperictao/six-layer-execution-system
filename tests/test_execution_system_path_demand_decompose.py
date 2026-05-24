#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from test_workspace_clone import cloned_workspace, init_git_repo, workspace_env


def run(workspace: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(workspace / "scripts" / "exec_sys.py"), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
        cwd=workspace,
    )


def run_script(workspace: Path, env: dict[str, str], script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(workspace / "scripts" / script), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
        cwd=workspace,
    )


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def extract_value(output: str, key: str) -> str:
    prefix = f"- {key}: "
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise AssertionError(f"missing key {key}\n{output}")


def expect_ok(name: str, proc: subprocess.CompletedProcess[str], needle: str | None = None) -> str:
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass\n{output}")
    if needle:
        expect(output, needle)
    return output


def expect_fail(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    output = proc.stdout + proc.stderr
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail\n{output}")
    expect(output, needle)


def read_activity_card(workspace: Path, activity_id: str) -> str:
    card_path = workspace / "activities" / activity_id / "card.md"
    if not card_path.exists():
        raise AssertionError(f"missing activity card: {card_path}")
    return card_path.read_text(encoding="utf-8")


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        output = expect_ok(
            "decompose-default",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "Add demand decomposition command",
                "--request",
                "Implement a command that turns a natural-language request into generated demands, roadmap, tasks, and ACTIVE artifacts while keeping ACTIVE as the only runtime truth.",
            ),
            "DEMAND_DECOMPOSE_OK",
        )
        demand_doc = workspace / extract_value(output, "demand_doc")
        roadmap_doc = workspace / extract_value(output, "roadmap_doc")
        tasks_doc = workspace / extract_value(output, "tasks_doc")
        activity_id = extract_value(output, "activity_id")

        if not demand_doc.exists() or not roadmap_doc.exists() or not tasks_doc.exists():
            raise AssertionError("generated artifact files must exist")

        active_text = (workspace / "ACTIVE.md").read_text(encoding="utf-8")
        expect(active_text, f"| {activity_id} | roadmap |")
        card_text = read_activity_card(workspace, activity_id)
        expect(card_text, f"- activity_id: `{activity_id}`")

        demand_check = expect_ok(
            "demand-check",
            run_script(workspace, env, "check_demand_card_schema.py", str(demand_doc)),
            "DEMAND_CARD_SCHEMA_CHECK_OK",
        )
        expect(demand_check, "- scanned_files: 1")
        expect(output, "- strategy: implementation-standard")
        expect(output, "- autopilot: true")
        expect(output, "- confirmation_required_for_activation: false")

        expect_ok(
            "slice-schema",
            run_script(workspace, env, "check_task_slice_schema.py", str(tasks_doc)),
            "TASK_SLICE_SCHEMA_CHECK_OK",
        )
        expect_ok(
            "dependency-check",
            run_script(workspace, env, "check_task_dependency_graph.py", str(tasks_doc)),
            "TASK_DEPENDENCY_GRAPH_CHECK_OK",
        )
        expect_ok(
            "parallel-check",
            run_script(workspace, env, "check_parallel_safety.py", str(tasks_doc)),
            "PARALLEL_SAFETY_CHECK_OK",
        )
        expect_ok(
            "generated-consistency",
            run_script(workspace, env, "check_generated_decomposition_consistency.py"),
            "GENERATED_DECOMPOSITION_CONSISTENCY_CHECK_OK",
        )
        runner_output = expect_ok(
            "checks-runner",
            run_script(workspace, env, "run_execution_system_checks.py"),
            "EXECUTION_SYSTEM_CHECKS_OK",
        )
        resolved_tasks_doc = tasks_doc.resolve()
        expect(
            runner_output,
            f"==> python3 {(workspace / 'scripts' / 'check_task_slice_schema.py').resolve()} {resolved_tasks_doc}",
        )
        expect(
            runner_output,
            f"==> python3 {(workspace / 'scripts' / 'check_task_dependency_graph.py').resolve()} {resolved_tasks_doc}",
        )
        expect(
            runner_output,
            f"==> python3 {(workspace / 'scripts' / 'check_parallel_safety.py').resolve()} {resolved_tasks_doc}",
        )
        expect(runner_output, "- advisory_commands_run: 1")
        expect(runner_output, "- advisory_hits: 0")

        tasks_doc.write_text(
            tasks_doc.read_text(encoding="utf-8").replace("- rollback_strategy:", "- missing_rollback_strategy:", 1),
            encoding="utf-8",
        )
        broken_runner = run_script(workspace, env, "run_execution_system_checks.py")
        broken_output = broken_runner.stdout + broken_runner.stderr
        if broken_runner.returncode == 0:
            raise AssertionError(f"generated tasks drift should fail the runner\n{broken_output}")
        expect(broken_output, "EXECUTION_SYSTEM_CHECKS_FAILED")
        expect(
            broken_output,
            f"- first_failing_command: python3 {(workspace / 'scripts' / 'check_task_slice_schema.py').resolve()} {resolved_tasks_doc}",
        )

        expect_fail(
            "conflict-on-second-run",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "Add demand decomposition command",
                "--request",
                "Implement a command that turns a natural-language request into generated demands, roadmap, tasks, and ACTIVE artifacts while keeping ACTIVE as the only runtime truth.",
            ),
            "DEMAND_DECOMPOSE_CONFLICT",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        output = expect_ok(
            "decompose-activate",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "Activate generated activity",
                "--request",
                "Create a docs-first generated backlog and activate it immediately.",
                "--activate",
            ),
            "DEMAND_DECOMPOSE_OK",
        )
        activity_id = extract_value(output, "activity_id")
        expect(output, "- activated: true")
        expect(output, "- autopilot: true")
        active_text = (workspace / "ACTIVE.md").read_text(encoding="utf-8")
        expect(active_text, f"- current_focus_activity_id: `{activity_id}`")
        expect_ok(
            "active-consistency-after-activate",
            run_script(workspace, env, "check_active_consistency.py"),
            "CONSISTENCY_CHECK_OK",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        output = expect_ok(
            "decompose-high-risk-no-confirm",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "Production migration",
                "--request",
                "Create a production database schema migration backlog and activate it immediately.",
                "--activate",
            ),
            "DEMAND_DECOMPOSE_OK",
        )
        activity_id = extract_value(output, "activity_id")
        expect(output, "- strategy: implementation-review-gate")
        expect(output, "- activated: false")
        expect(output, "- status: blocked")
        expect(output, "- autopilot: false")
        expect(output, "- confirmation_required_for_activation: true")
        expect(output, "- activation_blocked_reason: manual review or explicit confirmation required before activation")
        active_text = (workspace / "ACTIVE.md").read_text(encoding="utf-8")
        expect(active_text, "- current_focus_activity_id: `waiting-ledger-review`")
        expect(active_text, f"| {activity_id} | roadmap |")
        expect(read_activity_card(workspace, activity_id), f"- activity_id: `{activity_id}`")
        expect_ok(
            "generated-consistency-high-risk-no-confirm",
            run_script(workspace, env, "check_generated_decomposition_consistency.py"),
            "GENERATED_DECOMPOSITION_CONSISTENCY_CHECK_OK",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        output = expect_ok(
            "decompose-high-risk-confirmed",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "Production migration",
                "--request",
                "Create a production database schema migration backlog and activate it immediately.",
                "--activate",
                "--confirm",
            ),
            "DEMAND_DECOMPOSE_OK",
        )
        activity_id = extract_value(output, "activity_id")
        expect(output, "- activated: true")
        expect(output, "- status: ready")
        expect(output, "- autopilot: false")
        expect(output, "- confirmation_required_for_activation: true")
        expect(output, "- activation_blocked_reason: none")
        active_text = (workspace / "ACTIVE.md").read_text(encoding="utf-8")
        expect(active_text, f"- current_focus_activity_id: `{activity_id}`")
        expect_ok(
            "active-consistency-after-high-risk-activate",
            run_script(workspace, env, "check_active_consistency.py"),
            "CONSISTENCY_CHECK_OK",
        )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)

        output = expect_ok(
            "decompose-readable-default-slug",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "真实需求演练报告链路",
                "--request",
                "新增 demand roadmap tasks closeout 报告链路，并保持 ACTIVE 为唯一运行态真相。",
            ),
            "DEMAND_DECOMPOSE_OK",
        )
        demand_doc = extract_value(output, "demand_doc")
        if "request-" in demand_doc:
            raise AssertionError(f"mixed-language request should not fall back to opaque request hash\n{output}")

        output = expect_ok(
            "decompose-explicit-slug",
            run(
                workspace,
                env,
                "demand",
                "decompose",
                "--title",
                "另一个中文标题",
                "--slug",
                "realistic-demand-report",
                "--request",
                "新增一条真实需求演练链路，并保持 ACTIVE 为唯一运行态真相。",
            ),
            "DEMAND_DECOMPOSE_OK",
        )
        expect(output, "- demand_doc: activities/auto-realistic-demand-report/0-demand.md")
        expect(output, "realistic-demand-report")

    print("EXECUTION_SYSTEM_DEMAND_DECOMPOSE_PATH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
