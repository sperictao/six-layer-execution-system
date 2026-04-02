#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from execution_system_paths import WORKSPACE
SPEC = WORKSPACE / "docs/execution-system-spec-v1.md"
ROADMAP = WORKSPACE / "roadmaps/execution-system-spec-v1-roadmap.md"
TASKS = WORKSPACE / "tasks/execution-system-spec-v1-tasks.md"
ACTIVE = WORKSPACE / "ACTIVE.md"
HEARTBEAT = WORKSPACE / "HEARTBEAT.md"


def expect_contains(text: str, needle: str, scope: str, problems: list[str]) -> None:
    if needle not in text:
        problems.append(f"{scope}: missing `{needle}`")


def main() -> int:
    spec = SPEC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    tasks = TASKS.read_text(encoding="utf-8")
    active = ACTIVE.read_text(encoding="utf-8")
    heartbeat = HEARTBEAT.read_text(encoding="utf-8")

    problems: list[str] = []

    expect_contains(spec, "maintenance mode", "spec", problems)
    expect_contains(spec, "Reopen conditions", "spec", problems)
    expect_contains(spec, "Re-entry protocol", "spec", problems)
    expect_contains(spec, "Resume-style trigger rule", "spec", problems)
    expect_contains(spec, "do not answer task-status or task-resume questions from conversational memory alone", "spec", problems)

    expect_contains(roadmap, "Maintenance mode", "roadmap", problems)
    expect_contains(roadmap, "ES-F.F33", "roadmap", problems)

    expect_contains(tasks, "Slice F31 - define reopen conditions for future execution-system work", "tasks", problems)
    expect_contains(tasks, "Slice F32 - define maintenance-mode re-entry protocol", "tasks", problems)
    expect_contains(tasks, "Slice F33 - plan acceptance / summary / closeout integration wave", "tasks", problems)

    expect_contains(active, "status: `parked`", "ACTIVE", problems)
    expect_contains(active, "maintenance mode until a concrete reopen trigger appears", "ACTIVE", problems)
    expect_contains(active, "current_slice_id: `ES-F.F33`", "ACTIVE", problems)

    expect_contains(heartbeat, "heartbeat 与人工触发必须遵守同一套恢复规则", "HEARTBEAT", problems)
    expect_contains(heartbeat, "与人工收到 `go` / `continue` / `继续` / `resume` / `next` / `start` 时的恢复顺序保持一致", "HEARTBEAT", problems)
    expect_contains(heartbeat, "heartbeat 不得仅凭聊天记忆、旧通知或旧 daily note 推断当前任务状态", "HEARTBEAT", problems)
    expect_contains(heartbeat, "heartbeat 内的执行规划也必须与人工执行遵守同一套并行调度口径", "HEARTBEAT", problems)
    expect_contains(heartbeat, "将无前置依赖、且无写冲突的子任务按同一波次并行处理", "HEARTBEAT", problems)
    expect_contains(heartbeat, "若存在硬依赖链、共享写目标、或后续决策依赖前一步输出，则必须保持串行", "HEARTBEAT", problems)

    if problems:
        print("EXECUTION_SYSTEM_GOVERNANCE_CONSISTENCY_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("EXECUTION_SYSTEM_GOVERNANCE_CONSISTENCY_OK")
    print("- maintenance_mode: documented")
    print("- reopen_conditions: documented")
    print("- reentry_protocol: documented")
    print("- resume_trigger_rule: documented")
    print("- heartbeat_recovery_alignment: documented")
    print("- heartbeat_parallel_dispatch_alignment: documented")
    print("- parked_activity_state: documented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
