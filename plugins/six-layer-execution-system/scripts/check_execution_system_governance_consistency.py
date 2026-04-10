#!/usr/bin/env python3
from __future__ import annotations


from execution_system_paths import WORKSPACE

SPEC = WORKSPACE / "docs/execution-system-spec-v1.md"
ROADMAP = WORKSPACE / "roadmaps/execution-system-spec-v1-roadmap.md"
TASKS = WORKSPACE / "tasks/execution-system-spec-v1-tasks.md"
ACTIVE = WORKSPACE / "ACTIVE.md"
ACCEPTANCE = WORKSPACE / "docs/execution-system-spec-v1-acceptance-checklist.md"
SKILL = WORKSPACE / "skills" / "six-layer-execution-system" / "SKILL.md"
DELETED_PROMPT_FILES = [
    "AG" "ENTS.md",
    "HEART" "BEAT.md",
    "MEM" "ORY.md",
    "SO" "UL.md",
    "TO" "OLS.md",
]


def expect_contains(text: str, needle: str, scope: str, problems: list[str]) -> None:
    if needle not in text:
        problems.append(f"{scope}: missing `{needle}`")


def main() -> int:
    spec = SPEC.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    tasks = TASKS.read_text(encoding="utf-8")
    active = ACTIVE.read_text(encoding="utf-8")
    acceptance = ACCEPTANCE.read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")

    problems: list[str] = []

    expect_contains(spec, "maintenance mode", "spec", problems)
    expect_contains(spec, "Reopen conditions", "spec", problems)
    expect_contains(spec, "Re-entry protocol", "spec", problems)
    expect_contains(spec, "Resume-style trigger rule", "spec", problems)
    expect_contains(spec, "do not answer task-status or task-resume questions from conversational memory alone", "spec", problems)
    expect_contains(
        spec,
        "`skills/six-layer-execution-system/SKILL.md` is the single prompt-rule source of truth",
        "spec",
        problems,
    )

    expect_contains(roadmap, "Maintenance mode", "roadmap", problems)
    expect_contains(roadmap, "ES-F.F33", "roadmap", problems)

    expect_contains(tasks, "Slice F31 - define reopen conditions for future execution-system work", "tasks", problems)
    expect_contains(tasks, "Slice F32 - define maintenance-mode re-entry protocol", "tasks", problems)
    expect_contains(tasks, "Slice F33 - plan acceptance / summary / closeout integration wave", "tasks", problems)

    expect_contains(active, "status: `parked`", "ACTIVE", problems)
    expect_contains(active, "maintenance mode until a concrete reopen trigger appears", "ACTIVE", problems)
    expect_contains(active, "current_slice_id: `ES-F.F33`", "ACTIVE", problems)
    expect_contains(
        active,
        "roadmap_closeout_entrypoint: `scripts/complete_slice.py`",
        "ACTIVE",
        problems,
    )

    expect_contains(skill, "skills/six-layer-execution-system/SKILL.md` is the only prompt-rule source of truth", "skill", problems)
    expect_contains(skill, "默认中文回复", "skill", problems)
    expect_contains(skill, "恢复型触发必须遵守同一套恢复规则", "skill", problems)
    expect_contains(skill, "对 `go` / `continue` / `继续` / `resume` / `next` / `start` 这类恢复型触发来说", "skill", problems)
    expect_contains(skill, "恢复型触发不得仅凭聊天记忆、旧 daily note 推断当前任务状态", "skill", problems)
    expect_contains(skill, "恢复型触发后的执行规划必须与人工执行遵守同一套并行调度口径", "skill", problems)
    expect_contains(skill, "将无前置依赖、且无写冲突的子任务按同一波次并行处理", "skill", problems)
    expect_contains(skill, "若存在硬依赖链、共享写目标、或后续决策依赖前一步输出，则必须保持串行", "skill", problems)
    expect_contains(skill, "`scripts/complete_slice.py` is the canonical closeout entrypoint", "skill", problems)
    expect_contains(skill, "`python3 scripts/run_execution_checks.py checks --timeout 60`", "skill", problems)

    expect_contains(acceptance, "- `skills/six-layer-execution-system/SKILL.md`", "acceptance", problems)
    if any(name in acceptance for name in DELETED_PROMPT_FILES):
        problems.append("acceptance: deleted prompt files still referenced")

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
    print("- prompt_authority: documented")
    print("- skill_recovery_alignment: documented")
    print("- skill_parallel_dispatch_alignment: documented")
    print("- parked_activity_state: documented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
