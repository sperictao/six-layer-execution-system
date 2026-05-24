# ACTIVE.md — Execution Ledger v3

## Ledger meta
- version: `3`
- mode: `multi-activity`
- current_focus_activity_id: `none`
- default_reply_activity_id: `none`
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

## Focus: none
- status: `none`

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
- `recycle/` — 已确认回收的 activity 目录与 `history.md` 索引，不是运行态真相

## Recovery checklist
1. Read `Ledger meta` and `Activity index` above.
2. If `current_focus_activity_id` is `none`, there is no live activity; use `recycle/history.md` only as historical index.
3. Otherwise follow `Focus` pointer to `activities/<focus>/card.md`.
4. Read the card — follow `2-roadmap.md` and `3-tasks/<slice>.md`.
5. Run: `python3 scripts/run_execution_system_checks.py checks --timeout 60`
6. For progress questions, verify repo facts before answering.
