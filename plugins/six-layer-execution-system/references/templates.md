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

## 3. Tasks template

```md
# <project> tasks

## Current phase
- ...

## PR queue

### PR-A - <name>
- goal:
  - ...
- validation:
  - ...
- done_definition:
  - ...
- risk:
  - low|medium|high

#### Slice A1 - <name>
- phase_id: `PH-A`
- goal:
  - ...
- scope:
  - ...
- target_files:
  - ...
- depends_on:
  - ...
- parallel_safe:
  - `true|false`
- shared_write_targets:
  - ...
- expected_artifacts:
  - ...
- integration_notes:
  - ...
- handoff_output:
  - ...
- validation:
  - ...
- done_definition:
  - ...
- rollback_strategy:
  - ...
- risk:
  - low|medium|high
```

Rules:
- tasks own slice design and validation
- slices may include dependency and parallel-safety metadata when the work is complex enough to need DAG semantics
- every slice should be independently reviewable and rollbackable
- do not use tasks as the current runtime truth

---

## 4. ACTIVE ledger meta template

```md
## Ledger meta
- version: `2`
- mode: `multi-activity`
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
- tasks_doc: `...`
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
