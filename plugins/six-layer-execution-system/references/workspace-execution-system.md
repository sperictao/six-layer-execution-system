# Workspace Execution System

## Primary Local Sources

Read these first when the task is about the local execution system:

- `<plugin-root>/skills/six-layer-execution-system/SKILL.md`
- `<plugin-root>/ACTIVE.md`
- `<plugin-root>/docs/execution-system-spec-v1.md`
- `<plugin-root>/docs/execution-system-maintenance-guardrails.md`
- `<repo-root>/tests/execution-system-testing-inventory.md`
- `<plugin-root>/docs/execution-system-testing-inventory.md` (compatibility pointer)

## Core Model

The local plugin-hosted execution system is built on:

- layered truth
- focus-first execution
- explicit completion protocol

The six owned layers are:

1. contract: long-lived constraints and invariants
2. roadmap: phases, dependencies, exit criteria
3. tasks: individual slice plan/outcome files under `activities/<activity-id>/3-tasks/<slice-id>.md`
4. ACTIVE: current runtime truth
5. decisions: durable rationale
6. memory: history and recovery aids

Demand intake exists upstream of those layers but is not runtime truth.

## Runtime Truth Rules

- `skills/six-layer-execution-system/SKILL.md` is the only prompt-rule source of truth.
- `ACTIVE.md` is the only live answer to "what are we doing now?"
- Do not reconstruct current state from memory logs, daily notes, or chat history.
- Do not store current slice or live blockers in roadmap or memory files.
- Do not turn `ACTIVE.md` into a milestone diary.

When asked to recover or report status:

1. read `ACTIVE.md`
2. if the focus activity is `none`, report the ledger as idle and use `recycle/history.md` only as historical context
3. otherwise resolve the focus activity
4. read its card at `activities/<focus>/card.md`
5. read the linked `2-roadmap.md` and `3-tasks/<slice>.md` within the activity directory
6. only then reply

## Focus-First and Parallel-Wave Semantics

Default rule:

- only `current_focus_activity_id` may auto-advance
- non-focus activities may exist but must not silently run

Parallel execution is allowed only inside the current focus activity and only when:

- tasks do not write the same file or mutate the same runtime state
- each task has a clear input/output boundary
- the parent path owns the integration step

Prefer serial execution when:

- work is a hard dependency chain
- tasks touch overlapping file regions
- later choices depend on earlier outputs

`ACTIVE.md` may carry wave-state fields only when the focus activity is truly using
parallel-wave execution:

- `execution_mode`
- `current_wave_id`
- `ready_slices`
- `inflight_slices`
- `blocked_slices`
- `integration_step`
- `last_wave_result`

Otherwise keep ACTIVE lean.

## Completion Contract

The local system treats completion as explicit artifact state, not inference.

Required semantics:

- `validation_state: validated`
- `slice_state: closed_out`

Do not regress to implicit completion inferred from:

- green validation list alone
- git cleanliness alone
- a human summary alone

## Closeout and Handoff Flow

The canonical flow is implemented in `<plugin-root>/scripts/complete_slice.py`.

Flow summary:

1. `prepare`
2. `payload`
3. external host handoff, if needed

Durable closeout truth lives in the frozen closeout artifact, not in `ACTIVE.md`.
The canonical handoff payload should explicitly carry `current_focus_activity_id` from that artifact instead of re-reading live focus state.

## Activity Recycling

Completed activities can leave the live ledger after explicit user confirmation.

Rules:

- only `status: done` activities may be recycled
- current focus and default reply activities must not be recycled
- dry-run output must ask for confirmation and must not mutate files
- confirmed recycling removes the activity from `ACTIVE.md` Activity index
- confirmed recycling moves `activities/<activity-id>/` to `recycle/activities/<activity-id>/`
- `recycle/history.md` is the durable recycled-activity index

Recycled activity content is historical context, not live runtime truth. Recovery starts from `ACTIVE.md`, not from `recycle/history.md`.

If every activity has been force-recycled, `ACTIVE.md` may intentionally hold
`current_focus_activity_id: none`, an empty Activity index, and `Focus: none`.
That state means the execution ledger is idle; focus-dependent path tests are
not applicable until a new activity is created.

## Maintenance-Mode Guardrails

Once `execution-system-spec-v1` reached maintenance mode, local rules became:

- reopen only with a concrete trigger
- never weaken explicit `validated` / `closed_out`
- keep ACTIVE runtime-only
- make tests follow live runtime truth dynamically
- keep advisories actionable and non-blocking
- do not create new execution-system slices by default

Use the maintenance guardrails doc whenever a change risks reopening the line.

## Current Testing Philosophy

The local system prefers:

- precise checkers for hard-fail runtime truth
- advisory scripts for non-blocking operator hints
- path tests for protocol drift
- one unified checker runner
- one unified full-test runner

Use smoke tests for local field invariants.
Use synthetic path tests when a value must survive multiple surfaces such as:

- artifact -> payload
- runner -> acceptance
- focus state -> closeout-ready gate

See `references/checkers-and-protocols.md` for the concrete script map.
