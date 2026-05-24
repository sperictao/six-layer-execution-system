# Execution System Templates

These templates are the canonical starting points for complex work in this workspace.

Use them to keep contract / roadmap / tasks / ACTIVE aligned without creating duplicate truth.

---

## 0. Demand Intake template

```md
# <topic> demand intake

- request:
- task_type: `implementation|refactor|governance|testing|docs|coordination|simple`
- desired_outcome:
- scope:
- constraints:
  - ...
- non_goals:
  - ...
- risk_level: `low|medium|high`
- external_confirmation_required: `true|false`
- dependency_graph:
  - ...
- parallelizable_units:
  - ...
- serial_units:
  - ...
- expected_artifacts:
  - ...
- validation_plan:
  - ...
- closeout_condition:
  - ...
```

Rules:
- demand intake is an upstream decomposition artifact, not runtime truth
- use it for complex work before expanding into contract / roadmap / tasks / ACTIVE
- do not duplicate current live state here; `ACTIVE.md` remains the only runtime truth

---

## 1. Contract template

```md
# <project> contract

## Goal
- ...

## Scope
- ...

## Invariants
- ...

## Non-goals
- ...

## Forbidden moves
- ...

## Allowed tradeoffs
- ...

## Validation baseline
- ...

## Completion philosophy
- ...

## Decomposition Guardrails
- allowed_slice_shapes:
  - ...
- forbidden_slice_shapes:
  - ...
- preferred_dependency_shape:
  - ...
- parallelism_policy:
  - ...
- integration_constraints:
  - ...

## Review triggers
- ...
```

---

## 2. Roadmap template

```md
# <project> roadmap

## Goal
- ...

## Contract reference
- contracts/<project>-contract.md

## Validation baseline
- ...

## Phases

### Phase 1 - <name>
- objective:
  - ...
- dependencies:
  - ...
- outputs:
  - ...
- exit criteria:
  - ...
- decomposition_strategy:
  - ...
- recommended_wave_shape:
  - `serial|parallel-wave|mixed`
- risks:
  - ...

### Phase 2 - <name>
- objective:
  - ...
- dependencies:
  - ...
- outputs:
  - ...
- exit criteria:
  - ...
- decomposition_strategy:
  - ...
- recommended_wave_shape:
  - `serial|parallel-wave|mixed`
- risks:
  - ...

## Current recommended phase
- ...
```

Rules:
- roadmap owns phase structure, not live runtime state
- roadmap may describe decomposition strategy and recommended wave shape at the phase level
- roadmap must not describe current live wave, inflight slices, or alternate runtime truth
- do not store current commit / inflight handoff / daily progress in roadmap

---

## 3. Tasks: single-slice file template

Each slice gets its own independent file under `tasks/<activity-id>/<slice-id>.md`.
The file is the **plan artifact** for that slice — written before execution, updated after completion.

```md
# Slice <slice-id> — <名称>

- activity_id: `<activity-id>`
- phase_id: `<PH-X>`
- status: `ready`
- goal:
  - ...
- scope:
  - ...
- target_files:
  - ...
- actual_execution_plan:
  - Step 1: ...
  - Step 2: ...
  - Step 3: 验证...
- depends_on:
  - ...
- parallel_safe: `true|false`
- shared_write_targets:
  - ...
- expected_artifacts:
  - ...
- integration_notes:
  - ...
- validation:
  - ...
- done_definition:
  - ...
- rollback_strategy:
  - ...
- risk: `low|medium|high`
- actual_outcome:
  - commit: ...
  - verification: ...
```

Fields:

| 字段 | 何时填写 | 说明 |
|------|---------|------|
| `status` | 始终 | `ready` → `in_progress` → `done` |
| `actual_execution_plan` | **执行前必填** | 完整执行计划，含步骤和验证，不可只口头陈述 |
| `actual_outcome` | 完成后填写 | commit + verification 结果 |

Rules:

- 每个 slice 一个独立文件，文件名即 slice 标识（如 `P0-1.md`）
- `actual_execution_plan` 必须在用户确认前写入文件
- 执行中若发现与初始评估不符，立即更新此文件
- 完成后填写 `actual_outcome`，将 `status` 改为 `done`
- 并行 wave 中，无写冲突的 slice 可同时执行
- 文件的结束即是 slice 的完成——不需要额外 closeout 记录

---

## 4. Activity directory template (v3)

Each activity lives in `activities/<activity-id>/`:

```
activities/<activity-id>/
  card.md          ← 活动卡片（必选）
  0-demand.md      ← 需求摄入（可选）
  1-contract.md    ← 合约（可选）
  2-roadmap.md     ← 路线图（roadmap 类型必选）
  3-tasks/         ← 任务切片文件（roadmap 类型必选）
  4-decisions/     ← 决策记录（可选）
  5-memory/        ← 活动记忆（可选）
```

### 4.1 card.md template

```md
### Activity: <activity-id>
- activity_id: `<activity-id>`
- title: `...`
- type: `roadmap|waiting|simple`
- owner: `...`
- status: `ready|in_progress|blocked|parked|done`
- priority: `P1|P2|P3`
- autopilot: `true|false`
- focus_rank: `<int>`
- path: `<repo path or .>`
- repo: `<repo name>`
- source_doc: `activities/<activity-id>/0-demand.md`
- roadmap_doc: `activities/<activity-id>/2-roadmap.md`
- tasks_dir: `activities/<activity-id>/3-tasks/`
- tasks_doc: `activities/<activity-id>/3-tasks/`
- current_tasks_file: `activities/<activity-id>/3-tasks/<slice>.md`
- current_slice_id: `<slice-id>`
- next_slice_id: `<slice-id>`
- objective: `...`
- done_when:
  - ...
- next_step:
  - ...
- validation:
  - ...
- last_commit: `<commit>`
- blocked_by:
  - none
- retrieval_keys:
  - ...
- query_recipe:
  - ...
- last_decision:
  - ...
- done_definition:
  - ...
- notes:
  - ...
```

## 5. ACTIVE ledger meta template (v3)

```md
# ACTIVE.md — Execution Ledger v3

## Ledger meta
- version: `3`
- mode: `multi-activity`
- current_focus_activity_id: `<activity-id>`
- default_reply_activity_id: `<activity-id>`
- selection_policy: `focus-first`
- activity_root: `activities/`
- updated_at: `<timestamp>`

## Status legend
- ...

## Activity index

| activity_id | type | status | priority | path |
|------------|------|--------|----------|------|
| <id> | roadmap | in_progress | P1 | activities/<id>/ |

## Focus: <activity-id>
- card: `activities/<activity-id>/card.md`
- status: `<status>`
- current_slice_id: `<slice>`
- next_slice_id: `<slice>`
- last_commit: `<commit>`
```
- current_focus_activity_id: `<activity-id>`
- default_reply_activity_id: `<activity-id>`
- selection_policy: `focus-first`
- updated_at: `<timestamp>`
```

---

## 5. ACTIVE roadmap activity card template

```md
### Activity: <activity-id>
- activity_id: `<activity-id>`
- title: `...`
- type: `roadmap`
- owner: `...`
- status: `ready|in_progress|blocked|parked|done`
- priority: `P1|P2|P3`
- autopilot: `true|false`
- repo: `...`
- path: `...`
- roadmap_doc: `...`
- tasks_dir: `tasks/<activity-id>/`
- current_tasks_file: `tasks/<activity-id>/<slice-id>.md`
- current_slice_id: `...`
- next_slice_id: `...`
- objective: `...`
- done_when:
  - ...
- execution_mode: `serial|parallel-wave`
- current_wave_id: `...`
- ready_slices:
  - ...
- inflight_slices:
  - ...
- blocked_slices:
  - ...
- integration_step:
  - ...
- last_wave_result:
  - ...
- next_step:
  - ...
- validation:
  - ...
- blocked_by:
  - none
- last_commit: `...`
- last_validation:
  - ...
- retrieval_keys:
  - ...
- query_recipe:
  - ...
- last_artifact:
  - ...
- last_decision:
  - ...
- done_definition:
  - ...
- notes:
  - ...
```

Rules:
- current runtime truth lives here, not in roadmap/tasks/memory
- roadmap activities may be auto-runnable only if they are the focus activity and satisfy workspace rules
- wave-state fields are recommended only when the activity truly uses a parallel-wave execution model; do not add fake live-wave state to roadmap-only work

---

## 6. ACTIVE waiting activity card template

```md
### Activity: <activity-id>
- activity_id: `<activity-id>`
- title: `...`
- type: `waiting`
- owner: `...`
- status: `blocked|parked`
- priority: `P1|P2|P3`
- autopilot: `false`
- waiting_on: `user|external|time`
- unblock_condition: `...`
- next_step:
  - ...
- validation:
  - ...
- blocked_by:
  - ...
- retrieval_keys:
  - ...
- query_recipe:
  - ...
- last_artifact:
  - ...
- last_decision:
  - ...
- done_definition: `...`
- notes:
  - ...
```

Rules:
- waiting activities must never be counted as auto-runnable
- do not include roadmap-only fields like `current_slice_id` or `last_commit`

---

## 7. ACTIVE simple activity card template

```md
### Activity: <activity-id>
- activity_id: `<activity-id>`
- title: `...`
- type: `simple`
- owner: `...`
- status: `ready|in_progress|blocked|parked|done`
- priority: `P1|P2|P3`
- autopilot: `true|false`
- goal: `...`
- scope: `...`
- next_step:
  - ...
- validation:
  - ...
- blocked_by:
  - none
- retrieval_keys:
  - ...
- query_recipe:
  - ...
- last_artifact:
  - ...
- last_decision:
  - ...
- done_definition: `...`
- notes:
  - ...
```

Rules:
- simple activities do not require repo/slice/commit semantics
- they still need explicit goal, next step, and validation

---

## 8. Decision template

```md
# Decision: <title>

- date: YYYY-MM-DD
- project: <project>
- status: accepted|superseded|proposed

## Context
- ...

## Options considered
- A
- B
- C

## Chosen
- ...

## Why
- ...

## Rejected because
- ...

## Review trigger
- ...
```

---

## 9. Slice closeout checklist

Use this when deciding whether a roadmap slice is truly complete.

- [ ] code / change landed
- [ ] validation passed
- [ ] commit recorded
- [ ] ACTIVE switched to next slice atomically
- [ ] closeout artifact created
- [ ] canonical handoff payload derivable from the frozen closeout artifact

Rule:
- only closed-out slices may be announced externally as complete
