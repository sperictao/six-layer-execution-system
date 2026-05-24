# ACTIVE.md — Execution Ledger v3

## Ledger meta
- version: `3`
- mode: `multi-activity`
- current_focus_activity_id: `waiting-ledger-review`
- default_reply_activity_id: `waiting-ledger-review`
- selection_policy: `focus-first`
- activity_root: `activities/`
- updated_at: `2026-05-24 CST`

## Status legend
- `ready` — agreed and ready to start
- `in_progress` — actively being worked on
- `blocked` — cannot proceed until something changes
- `done` — completed and verified
- `parked` — intentionally paused

## Activity index

| activity_id | type | status | priority | path |
|------------|------|--------|----------|------|
| ledger-v3-activity-isolation | roadmap | done | P1 | activities/ledger-v3-activity-isolation/ |
| one-publish-architecture-fix | roadmap | done | P1 | activities/one-publish-architecture-fix/ |
| execution-system-spec-v1 | roadmap | parked | P1 | activities/execution-system-spec-v1/ |
| execution-system-decomposition-upgrade | roadmap | ready | P2 | activities/execution-system-decomposition-upgrade/ |
| active-ledger-v2 | roadmap | done | P1 | activities/active-ledger-v2/ |
| execution-system-testing | roadmap | done | P2 | activities/execution-system-testing/ |
| waiting-ledger-review | waiting | blocked | P2 | activities/waiting-ledger-review/ |
| simple-ledger-docs | simple | ready | P3 | activities/simple-ledger-docs/ |
| auto-auto-decompose-natural-language-demand | roadmap | blocked | P1 | activities/auto-auto-decompose-natural-language-demand/ |

## Focus: waiting-ledger-review
- card: `activities/waiting-ledger-review/card.md`
- status: `blocked`

## Workspace rules
- execution_truth: `ACTIVE.md` (this file) + `activities/<focus>/card.md`
- complex_task_truth: `activities/<id>/card.md` → `2-roadmap.md` → `3-tasks/`
- focus_execution: `focus-first`
- recovery_chain: `ACTIVE.md` → `activities/<focus>/card.md` → `3-tasks/<slice>.md`
- spec_reference: `docs/execution-system-spec-v1.md`

## Cross-activity resources
- `docs/` —跨 activity 规范与设计文档
- `references/` — 跨 activity 模板、协议、源映射
- `scripts/` — 跨 activity checker、runner、工具
- `skills/` — 跨 activity skill 定义
- `_archive/` — 已迁移的旧格式资源（保留备查）

## Recovery checklist
1. Read `Ledger meta` and `Activity index` above.
2. Follow `Focus` pointer to `activities/<focus>/card.md`.
3. Read the card — follow `2-roadmap.md` and `3-tasks/<slice>.md`.
4. Run: `python3 scripts/run_execution_system_checks.py checks --timeout 60`
5. For progress questions, verify repo facts before answering.
