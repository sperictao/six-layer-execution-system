#!/usr/bin/env python3
from __future__ import annotations


from execution_system_paths import WORKSPACE

SPEC = WORKSPACE / "docs/execution-system-spec-v1.md"
SPEC_ACTIVITY_ROOT = WORKSPACE / "activities/execution-system-spec-v1"
RECYCLED_SPEC_ACTIVITY_ROOT = WORKSPACE / "recycle/activities/execution-system-spec-v1"
ROADMAP = SPEC_ACTIVITY_ROOT / "2-roadmap.md"
TASKS = SPEC_ACTIVITY_ROOT / "3-tasks/execution-system-spec-v1-tasks.md"
ACTIVE = WORKSPACE / "ACTIVE.md"
CARD_SPEC_V1 = SPEC_ACTIVITY_ROOT / "card.md"
ACCEPTANCE = WORKSPACE / "docs/execution-system-spec-v1-acceptance-checklist.md"
README = WORKSPACE / "README.md"
ROOT_SKILL = WORKSPACE / "SKILL.md"
SOURCE_MAP = WORKSPACE / "references/source-map.md"
LOCAL_INSTALL = WORKSPACE / "references/local-install.md"
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


def read_activity_file(path, recycled_path):
    if path.exists():
        return path.read_text(encoding="utf-8")
    return recycled_path.read_text(encoding="utf-8")


def main() -> int:
    spec = SPEC.read_text(encoding="utf-8")
    roadmap = read_activity_file(ROADMAP, RECYCLED_SPEC_ACTIVITY_ROOT / "2-roadmap.md")
    tasks = read_activity_file(TASKS, RECYCLED_SPEC_ACTIVITY_ROOT / "3-tasks/execution-system-spec-v1-tasks.md")
    active = ACTIVE.read_text(encoding="utf-8")
    card_spec_v1 = read_activity_file(CARD_SPEC_V1, RECYCLED_SPEC_ACTIVITY_ROOT / "card.md")
    acceptance = ACCEPTANCE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    source_map = SOURCE_MAP.read_text(encoding="utf-8")
    local_install = LOCAL_INSTALL.read_text(encoding="utf-8")
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

    expect_contains(card_spec_v1, "status: `parked`", "execution-system-spec-v1 card", problems)
    expect_contains(card_spec_v1, "maintenance mode until a concrete reopen trigger appears", "execution-system-spec-v1 card", problems)
    expect_contains(card_spec_v1, "current_slice_id: `ES-F.F33`", "execution-system-spec-v1 card", problems)
    expect_contains(skill, "skills/six-layer-execution-system/SKILL.md` is the only prompt-rule source of truth", "skill", problems)
    expect_contains(skill, "默认中文回复", "skill", problems)
    expect_contains(skill, "恢复型触发必须遵守同一套恢复规则", "skill", problems)
    expect_contains(skill, "对 `go` / `continue` / `继续` / `resume` / `next` / `start` 这类恢复型触发来说", "skill", problems)
    expect_contains(skill, "恢复型触发不得仅凭聊天记忆、旧 daily note 推断当前任务状态", "skill", problems)
    expect_contains(skill, "恢复型触发后的执行规划必须与人工执行遵守同一套并行调度口径", "skill", problems)
    expect_contains(skill, "将无前置依赖、且无写冲突的子任务按同一波次并行处理", "skill", problems)
    expect_contains(skill, "若存在硬依赖链、共享写目标、或后续决策依赖前一步输出，则必须保持串行", "skill", problems)
    expect_contains(skill, "`scripts/complete_slice.py` is the canonical closeout entrypoint", "skill", problems)
    expect_contains(skill, "`local-state/last-slice-closeout.json`", "skill", problems)
    expect_contains(skill, "`activities/<activity-id>/3-tasks/<slice-id>.md`", "skill", problems)
    expect_contains(skill, "`python3 scripts/run_execution_checks.py checks --timeout 60`", "skill", problems)

    expect_contains(acceptance, "- `skills/six-layer-execution-system/SKILL.md`", "acceptance", problems)
    if any(name in acceptance for name in DELETED_PROMPT_FILES):
        problems.append("acceptance: deleted prompt files still referenced")
    if ROOT_SKILL.exists():
        problems.append("root-skill: root-level SKILL.md must not exist; keep prompt authority under skills/six-layer-execution-system/SKILL.md")

    expect_contains(readme, "`activities/<activity-id>/0-demand.md`", "README", problems)
    expect_contains(readme, "`recycle/` 保存已确认回收的历史 activity", "README", problems)
    expect_contains(source_map, "Current live activity state is not maintained in this source map", "source-map", problems)
    expect_contains(source_map, "recycle/activities/<activity-id>/", "source-map", problems)
    expect_contains(local_install, "`activities/` (new live activity directories)", "local-install", problems)
    expect_contains(local_install, "`local-state/` (ignored machine-local closeout and telemetry state)", "local-install", problems)

    stale_current_docs = {
        "README": readme,
        "source-map": source_map,
        "local-install": local_install,
    }
    forbidden_needles = [
        "`demands/*.md`",
        "`roadmaps/*-roadmap.md`",
        "`tasks/*-tasks.md`",
        "Current activities:",
        "_archive/",
        "memory/last-slice-closeout.json",
    ]
    for scope, text in stale_current_docs.items():
        for needle in forbidden_needles:
            if needle in text:
                problems.append(f"{scope}: stale runtime surface reference `{needle}`")

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
    print("- root_skill_shim: absent")
    print("- skill_recovery_alignment: documented")
    print("- skill_parallel_dispatch_alignment: documented")
    print("- parked_activity_state: documented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
