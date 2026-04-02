# execution system maintenance guardrails

## Purpose

This document defines the minimum guardrails for maintaining the execution system after
`execution-system-spec-v1` reached maintenance mode.

It exists to prevent the execution-system line from drifting back into:
- open-ended meta work
- duplicated runtime truth
- partial completion semantics
- noisy advisory growth
- brittle focus-dependent tests

---

## 1. Reopen only with a concrete trigger

Do not reopen the execution-system line just because more polish is possible.

A new execution-system slice should normally be opened only when at least one of these is true:
- a structural rule in the final model is still missing from real workflow or artifact semantics
- operators repeatedly hit the same recovery ambiguity across sessions
- a checker, advisory, or acceptance path produces confusing or misleading results more than once
- a real project migration exposes a gap that the current six-layer model cannot represent cleanly

Reasons that are not sufficient by themselves:
- "this could be a little cleaner"
- speculative automation ideas without repeated pain
- broad cleanup energy with no concrete runtime-truth or recovery problem

Review question:
- what is the concrete trigger?

---

## 2. Never weaken `validated` and `closed_out`

The execution system must keep explicit completion semantics in closeout artifacts.

Required fields:
- `validation_state: validated`
- `slice_state: closed_out`

Any future closeout, notification, or verifier change must preserve these semantics.
Do not move back to implicit completion inferred only from validation lists, git state, or human summary.

Primary files:
- `scripts/create_slice_closeout.py`
- `scripts/check_slice_closeout.py`
- `scripts/test_slice_closeout_state.py`

Review question:
- does this change make completion more explicit, or more implicit?

---

## 3. Keep ACTIVE as runtime truth, not a diary

`ACTIVE.md` should keep only runtime-recovery-critical information.

Keep content in `ACTIVE.md` when it directly answers:
- what is the current focus activity
- what slice is live now
- what should be validated next
- what is the current blocker
- what durable artifact or decision pointer is needed for recovery

Move content out of `ACTIVE.md` when it is mainly:
- a chronological milestone log
- repeated historical narrative
- rationale better stored in `decisions/`
- policy prose already captured in spec/docs

For roadmap activities:
- keep concise `last_artifact` pointers
- keep concise `last_decision` pointers
- do not turn either into a running diary

Primary files:
- `ACTIVE.md`
- `docs/execution-system-spec-v1.md`
- `memory/*.md`
- `decisions/`

Review question:
- is this line helping recovery, or just preserving history?

---

## 4. Tests must follow runtime truth dynamically

Tests for execution-system behavior should prefer deriving runtime facts from `ACTIVE.md`
instead of hard-coding a specific focus activity or fixed project assumption.

Especially sensitive areas:
- current focus activity id
- current focus doc pointers
- focus-first semantics
- maintenance-mode transitions
- autopilot and runnable-activity behavior

If a behavior depends on the current focus, the test should read the current focus from the ledger
instead of assuming a specific activity such as `execution-system-spec-v1`.

Primary files:
- `scripts/test_check_active_consistency.py`
- `scripts/test_run_execution_system_checks.py`
- any future focus-aware smoke tests

Review question:
- is this test validating the rule, or only today’s specific workspace state?

---

## 5. Advisory rules must stay actionable and non-blocking

Advisory rules are allowed only when they help action without pretending to be deterministic hard-fail rules.

Each advisory should provide:
- a concrete reason for the hit
- a recovery hint
- non-blocking semantics

Each advisory should avoid:
- fuzzy prose scoring
- silent promotion into hard-fail behavior
- repeated noise without operator value

When an advisory starts feeling noisy, tighten its trigger before expanding its message surface.
Do not compensate for weak signals with more verbose wording.

Primary files:
- `scripts/check_oversized_migration_slices.py`
- `scripts/test_check_oversized_migration_slices.py`
- `scripts/run_execution_system_checks.py`

Review question:
- does this advisory help the operator take a next step, or just sound smart?

---

## 6. Maintenance-mode operating rule

While the execution-system line is in maintenance mode:
- do not create new execution-system slices by default
- prefer spending execution capacity on the current business focus
- a first-class `waiting` focus is also valid when work is intentionally paused for human input; this should not be treated as a maintenance failure by itself
- reopen only through the documented reopen conditions and re-entry protocol
- if reopened, open one slice for one concrete trigger

This line should be treated as infrastructure in maintenance, not as a standing backlog.

Primary references:
- `docs/execution-system-spec-v1.md`
- `docs/execution-system-spec-v1-acceptance-checklist.md`
- `roadmaps/execution-system-spec-v1-roadmap.md`
- `tasks/execution-system-spec-v1-tasks.md`
- `ACTIVE.md`

---

## 7. Minimal review checklist

Before landing a future execution-system change, answer all five questions:
- what is the concrete trigger?
- does completion become more explicit or more implicit?
- is this content runtime truth or historical narrative?
- is the test dynamic against the current ledger state?
- does the advisory help action without adding noise?

If any answer is unclear, the change probably needs more shaping before landing.
