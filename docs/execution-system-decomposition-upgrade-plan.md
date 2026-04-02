# execution system decomposition upgrade plan

## Purpose

This document proposes a full upgrade path for the execution system's demand decomposition model.

The goal is to evolve the workspace from a strong layered execution ledger into a true decomposition and dispatch engine that can:
- classify incoming demands consistently
- preserve one-layer-one-truth boundaries
- express dependency graphs explicitly
- support safe parallel-wave execution inside the current focus activity
- validate decomposition quality rather than only execution results
- recover cleanly after interruption without reconstructing intent from chat history

The plan is designed to extend the current `contract + roadmap + tasks + ACTIVE` model rather than replace it.

---

## Target architecture

```text
Demand Intake
-> Contract
-> Roadmap
-> Tasks
-> ACTIVE
-> Validation / Closeout
```

### Design principles
- keep `ACTIVE.md` as the only runtime truth
- keep focus-first execution as the workspace-wide guardrail
- introduce dependency and wave semantics without duplicating runtime truth into roadmap
- prefer additive schema evolution over disruptive rewrites
- require each new decomposition feature to have validation coverage

---

## Layer 0 - Demand Intake

### Objective
Create a standard intake step for complex work before it is expanded into contract / roadmap / tasks / ACTIVE.

### New artifact
Recommended path:
- `demands/<date>-<topic>.md`

Alternative adoption path:
- preserve the same schema in an existing source doc until a dedicated `demands/` layer is worth formalizing

### Required schema
Each demand intake card should contain:
- `request`
- `task_type`
- `desired_outcome`
- `scope`
- `constraints`
- `non_goals`
- `risk_level`
- `external_confirmation_required`
- `dependency_graph`
- `parallelizable_units`
- `serial_units`
- `expected_artifacts`
- `validation_plan`
- `closeout_condition`

### Allowed task types
- `implementation`
- `refactor`
- `governance`
- `testing`
- `docs`
- `coordination`
- `simple`

### Role in the system
Demand Intake is not runtime truth.
It is the structured upstream source used to derive:
- long-lived constraints -> `contract`
- phase structure -> `roadmap`
- slice DAG -> `tasks`
- live execution state -> `ACTIVE`

### Non-goals
- do not turn every tiny task into a heavy intake ceremony
- do not duplicate runtime state here
- do not let demand cards replace roadmap/tasks for execution

---

## Layer 1 - Contract upgrade

### Objective
Extend contract files so they define decomposition guardrails, not only business constraints.

Status:
- initial schema landing started in `docs/execution-system-spec-v1.md`
- initial template landing started in `references/templates.md`

### New contract section
Recommended section title:
- `Decomposition Guardrails`

### New fields
- `allowed_slice_shapes`
- `forbidden_slice_shapes`
- `preferred_dependency_shape`
- `parallelism_policy`
- `integration_constraints`
- `review_triggers`

### Example semantics
- `allowed_slice_shapes`
  - single-goal slices
  - pure wiring / pure state / pure mapping slices
- `forbidden_slice_shapes`
  - slices that combine runtime semantics changes with broad UI changes
  - slices that mutate multiple high-risk layers at once
- `parallelism_policy`
  - only slices with no shared write targets may run in the same wave
- `integration_constraints`
  - define which layers must be re-validated together after a wave lands

### Outcome
Contract becomes the formal place that answers:
- what kinds of decomposition are allowed
- what kinds of decomposition are considered unsafe

---

## Layer 2 - Roadmap upgrade

### Objective
Keep roadmap phase-only, but make phase decomposition strategy explicit.

Status:
- initial schema landing started in `docs/execution-system-spec-v1.md`
- initial template and self-hosting roadmap examples started in `references/templates.md` and `roadmaps/execution-system-decomposition-upgrade-roadmap.md`

### New per-phase fields
- `decomposition_strategy`
- `recommended_wave_shape`

### Meaning
- `decomposition_strategy`
  - describes how this phase should be sliced
  - examples: `pure-split-first`, `checks-before-runner`, `docs-and-governance-first`
- `recommended_wave_shape`
  - one of:
    - `serial`
    - `parallel-wave`
    - `mixed`

### Rules
Roadmap may describe:
- phase dependency structure
- expected outputs
- wave shape guidance

Roadmap must not describe:
- current live wave
- inflight slices
- current runtime state
- notification state

### Outcome
Roadmap becomes the phase-level dependency skeleton while `ACTIVE` remains the runtime truth.

---

## Layer 3 - Tasks upgrade

### Objective
Evolve tasks from a slice list into an executable slice DAG definition.

Status:
- initial schema landing started in `docs/execution-system-spec-v1.md`
- initial template and self-hosting task example started in `references/templates.md` and `tasks/execution-system-decomposition-upgrade-tasks.md`

### Required new per-slice fields
- `depends_on`
- `parallel_safe`
- `shared_write_targets`
- `expected_artifacts`
- `integration_notes`
- `handoff_output`

### Field semantics
- `depends_on`
  - explicit upstream slice ids
- `parallel_safe`
  - `true` only when no conflicting writes or runtime-state conflicts exist
- `shared_write_targets`
  - files or runtime domains that would make same-wave execution unsafe
- `expected_artifacts`
  - files, decisions, reports, or outputs the slice should produce
- `integration_notes`
  - what the parent execution layer must merge after this slice returns
- `handoff_output`
  - expected return structure for sub-task completion

### Slice quality hard rules
Every slice should satisfy:
- one primary goal
- single entry point
- single rollback unit
- explicit validation
- explicit dependency shape
- explicit parallel safety
- explicit expected artifacts
- no opportunistic scope creep

### Outcome
Tasks become machine-checkable decomposition data, not just a human-readable backlog.

---

## Layer 4 - ACTIVE upgrade

### Objective
Preserve `ACTIVE.md` as runtime truth, but upgrade roadmap activities into live dispatch cards.

Status:
- initial schema landing started in `docs/execution-system-spec-v1.md`
- initial template landing started in `references/templates.md`
- workspace policy pointer added to `ACTIVE.md` to keep wave-state fields optional and runtime-only

### New roadmap activity fields
- `execution_mode`
- `current_wave_id`
- `ready_slices`
- `inflight_slices`
- `blocked_slices`
- `integration_step`
- `last_wave_result`

### Field semantics
- `execution_mode`
  - `serial` or `parallel-wave`
- `current_wave_id`
  - current execution wave label, such as `W1`
- `ready_slices`
  - slices that may run now
- `inflight_slices`
  - slices currently being executed
- `blocked_slices`
  - slices waiting on dependencies
- `integration_step`
  - required merge step after the current wave returns
- `last_wave_result`
  - concise summary of the previous wave output

### Rules
- these fields live only in `ACTIVE.md`
- roadmap/tasks must not become alternate runtime truth sources
- heartbeat and manual execution must both read these fields before dispatching work

### Outcome
`ACTIVE.md` becomes a dispatch console rather than a passive status ledger.

---

## Layer 5 - Validation and Closeout upgrade

### Objective
Connect wave-based execution to the existing validation and closeout protocol.

### New concepts
#### Wave Validation
Per-wave validation record should answer:
- which slices ran
- what validation commands were run
- whether conflicts were detected
- whether integration succeeded

#### Stage Closeout
After each wave:
- update `ACTIVE.md`
- refresh ready/inflight/blocked state
- record integration result
- run any required validation for that wave

### Closeout additions
A wave-aware closeout should require:
- wave integration completed
- inflight slices cleared or reconciled
- ready/blocked state refreshed
- validation results captured
- normal slice/notification closeout rules still satisfied when a roadmap slice is complete

### Outcome
Execution no longer jumps directly from "tasks ran" to "slice complete" without recording wave integration state.

---

## Checker roadmap

### Candidate checker queue
1. `scripts/check_demand_card_schema.py`
   - validates demand intake schema completeness
   - recommended implementation wave: after Demand Intake schema is stable in real use
2. `scripts/check_task_dependency_graph.py`
   - validates `depends_on` integrity and forbids dependency cycles
   - recommended implementation wave: first checker candidate in decomposition-engine v1
3. `scripts/check_parallel_safety.py`
   - validates `parallel_safe` against shared write targets
   - recommended implementation wave: first checker candidate in decomposition-engine v1
4. `scripts/check_active_wave_state.py`
   - validates `execution_mode/current_wave_id/ready/inflight/blocked/integration_step`
   - recommended implementation wave: after ACTIVE wave-state fields are proven on a pilot activity and a promotion gate is satisfied
5. `scripts/test_execution_system_path_parallel_wave.py`
   - verifies a representative parallel-wave path end to end
   - recommended implementation wave: after one low-risk pilot activity adopts wave-state semantics

### Recommended v1 checker cut
The first implementation wave should stay narrow:
- `check_task_dependency_graph.py`
- `check_parallel_safety.py`

Deferred from the first wave:
- `check_demand_card_schema.py` until the intake card is used by at least one real activity
- `check_active_wave_state.py` until wave-state fields are proven ergonomic in `ACTIVE.md`
- `test_execution_system_path_parallel_wave.py` until a pilot path exists that does not require risky workspace mutation

### Active wave-state promotion gate
`check_active_wave_state.py` should move from pilot-only status into the unified hard-fail runner only when all of the following are true:
- a real roadmap activity in `ACTIVE.md` uses wave-state fields without violating lean runtime-truth boundaries
- `check_active_wave_state.py` and `test_check_active_wave_state.py` pass against that pilot repeatedly
- acceptance docs and testing inventory explicitly document the pilot semantics and current non-runner status
- roadmap/tasks/ACTIVE agree on the current slice and runner-promotion intent
- no known schema drift remains between wave-state fields and the active-ledger parser/checkers
- the expected recovery hint for a future runner failure is clear enough to be actionable

### Promotion gate checklist for `DX-E.E3`
- [ ] pilot activity exists in real `ACTIVE.md` data, not only in synthetic smoke fixtures
- [ ] pilot wave-state remains lean and does not duplicate roadmap/tasks truth
- [ ] `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/check_active_wave_state.py` passes
- [ ] `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/test_check_active_wave_state.py` passes
- [ ] `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/check_active_consistency.py` passes with the pilot activity still active
- [ ] acceptance checklist documents the pilot semantics and current non-runner status
- [ ] testing inventory documents the pilot semantics and current non-runner status
- [ ] roadmap/tasks/ACTIVE all point at `DX-E.E2 -> DX-E.E3` consistently
- [ ] a runner failure recovery hint for `check_active_wave_state.py` has been drafted before integration work starts

### Draft recovery hint for future runner integration
If `check_active_wave_state.py` is later promoted into `run_execution_system_checks.py`, the expected recovery hint should be:
- `repair invalid ACTIVE wave-state fields or revert the pilot activity to lean non-wave execution before continuing`

This hint is intentionally narrow:
- first inspect the current focus roadmap activity in `ACTIVE.md`
- verify `execution_mode/current_wave_id/ready_slices/inflight_slices/blocked_slices/integration_step`
- remove or repair wave-state fields that violate the pilot contract
- if the activity no longer truly uses parallel-wave execution, revert it to lean non-wave state instead of forcing placeholder values

### Integration targets
These should eventually be wired into:
- `run_execution_system_checks.py`
- `run_execution_system_full_tests.py`
- acceptance checklist
- governance consistency tests where relevant

### Pilot path recommendation
The first pilot should use execution-system testing work, not business-repo runtime work.

Recommended pilot properties:
- low external risk
- mostly docs/scripts changes
- limited shared write surface
- easy rollback
- easy validation through existing runners

Recommended pilot candidate:
- a future execution-system testing slice that updates inventory/tasks/runner wiring without touching product runtime semantics

### First parallel-wave path test cut
The first `test_execution_system_path_parallel_wave.py` should stay intentionally narrow.

Minimal scope:
- start from a synthetic execution-system fixture, not a product repo
- model exactly one focus roadmap activity using `execution_mode: parallel-wave`
- model one wave with:
  - one `ready_slices` item
  - one `inflight_slices` item
  - one `integration_step`
- assert that wave-state parsing, focused validation, and closeout-facing state transitions remain coherent
- avoid multi-wave orchestration in the first cut

Fixture strategy:
- use a temporary synthetic `ACTIVE.md` fixture derived from the decomposition-upgrade pilot shape
- keep the fixture entirely inside workspace test harness scope
- do not require git mutation in product repos
- prefer direct checker/runner invocation over broad end-to-end environment setup

Explicit non-goals:
- do not execute product repo build/test commands as part of this path test
- do not simulate real business runtime semantics
- do not require background sub-agents or live external systems
- do not validate every possible wave-state permutation in v1
- do not replace existing checker smoke coverage

Go / no-go rule for the implementation wave:
- `go` only if the fixture stays synthetic, rollback is trivial, and the test adds new confidence beyond existing smoke tests
- `no-go` if the proposed test still depends on unstable runtime semantics, broad workspace mutation, or duplicated coverage with existing checker tests

Current recommendation after `DX-E.E4` discovery:
- `go`

Rationale:
- the fixture can stay entirely synthetic and derived from the existing decomposition-upgrade pilot shape
- the expected test would validate a coherent single-wave path that is not covered by checker smoke tests alone
- rollback remains trivial because the first cut only adds a new test file and does not change runtime behavior
- no product-repo runtime coupling is required for the first implementation wave

---

## Acceptance changes

### New acceptance expectations
The upgraded system should eventually satisfy all of the following:
- demand intake exists for complex work
- contract files define decomposition guardrails
- roadmap phases define decomposition strategy and recommended wave shape
- task slices declare dependencies and parallel safety
- `ACTIVE.md` tracks current wave state for roadmap activities that use parallel-wave mode
- checker suite validates dependency graph and parallel safety semantics
- heartbeat and manual execution use the same recovery and dispatch model
- at least one real activity completes a true parallel-wave -> integration -> validation -> closeout loop

### Acceptance deltas for decomposition-engine v1
The first acceptance wave should require only:
- demand intake schema landed in spec + templates
- contract decomposition guardrails landed in spec + templates
- roadmap decomposition strategy / wave-shape fields landed in spec + templates
- task DAG fields landed in spec + templates
- ACTIVE wave-state fields landed in spec + templates
- checker backlog is sequenced and the first checker cut is explicitly chosen
- pilot path is named and justified

The first acceptance wave should not yet require:
- a fully enforced demand-card checker
- a fully enforced active-wave-state checker
- a production-scale parallel-wave rollout across business-repo work

---

## Migration plan

The canonical execution backlog for this upgrade now lives in:
- `roadmaps/execution-system-decomposition-upgrade-roadmap.md`
- `tasks/execution-system-decomposition-upgrade-tasks.md`

### Phase A - Schema introduction
- extend spec with Demand Intake, dependency graph, and wave semantics
- add template examples
- add task-field guidance for `depends_on` / `parallel_safe`
- add ACTIVE-field guidance for wave state

### Phase B - Checker introduction
- land dependency graph checker
- land parallel safety checker
- land active wave-state checker
- wire smoke coverage for each

### Phase C - Pilot activity
- pilot on execution-system testing work before business-repo adoption
- use a low-risk path to validate wave-state ergonomics

### Phase D - Workflow adoption
- teach heartbeat to read wave-state fields
- teach manual execution recovery to read the same fields
- wire the new checkers into runner + full test suite
- update acceptance checklist and inventory docs

---

## Recommended v1 minimum

If only a minimal but high-value subset should land first, do these six changes:
1. add Demand Intake and wave model sections to the spec
2. require `depends_on` in migrated task slices
3. require `parallel_safe` in migrated task slices
4. add `execution_mode/current_wave_id/ready_slices/integration_step` to roadmap activities in `ACTIVE.md`
5. add `check_task_dependency_graph.py`
6. add `check_parallel_safety.py`

This v1 would move the system from a strong execution ledger to a first real decomposition engine.

---

## Governance-drift expansion candidates

Prioritized candidate set after the first implementation wave:

1. focus/acceptance gate alignment drift
- target drift:
  - tests and acceptance scripts assuming `FOCUS_VALIDATION_OK` when the expected runtime state is actually `OK_WITH_POLICY_GATES`
- why it matters:
  - this is the most likely place for future false failures when focus policy evolves
- suggested first cut:
  - strengthen policy-gate path coverage around `validate_focus_first.py` + `accept_active_ledger_v2.py`

2. maintenance-mode vs approved non-business focus drift
- target drift:
  - maintenance checks assuming only runnable business focus is valid, while the workspace may intentionally focus a guarded execution-system activity
- why it matters:
  - this already produced real test drift during the current wave
- suggested cut:
  - extend maintenance/governance docs and tests so approved non-business focus states are explicitly modeled
- implementation anchors:
  - `scripts/check_execution_system_maintenance_mode.py`
  - `scripts/test_execution_system_maintenance_mode.py`
  - `scripts/test_execution_system_path_maintenance_focus_drift.py`

### Recommended second governance-drift test cut
`governance-drift-test-cut-2` should target maintenance-mode vs approved non-business focus drift.

Reason:
- the drift already appeared in real workspace evolution, not just hypothetical policy change
- the path stays workspace-local and synthetic enough to keep rollback trivial
- it complements `governance-drift-test-cut-1` by covering the maintenance branch of governance semantics instead of the focus/acceptance branch

3. closeout-ready vs evolving focus activity drift
- target drift:
  - closeout-ready smoke/tests assuming a fixed focus activity or fixed slice ids instead of deriving expectations from the current execution truth
- why it matters:
  - this is a recurring source of brittle test churn after focus changes
- suggested cut:
  - define a more focus-aware closeout-ready expectation layer
- implementation anchors:
  - `scripts/check_closeout_ready.py`
  - `scripts/test_check_closeout_ready.py`
  - `scripts/test_execution_system_path_closeout_ready_focus_drift.py`

4. runner/summary hint drift
- target drift:
  - new checkers landing without a matching summary-footer recovery hint or without the test that locks the hint
- why it matters:
  - the execution system now depends on actionable recovery messaging, not just pass/fail
- suggested cut:
  - add governance coverage that pairs checker adoption with required summary-hint coverage
- implementation anchors:
  - `scripts/run_execution_system_checks.py`
  - `scripts/test_run_execution_system_checks.py`
  - `scripts/test_execution_system_path_runner_hint_drift.py`

### Recommended first governance-drift test cut
`governance-drift-test-cut-1` should target focus/acceptance gate alignment drift.

Reason:
- it has the highest chance of recurring as focus policy evolves
- it is narrow, synthetic, and workspace-local
- it does not require product-repo runtime coupling
- it complements the existing policy-gate coverage without duplicating checker smoke

Minimal cut shape:
- use synthetic or tightly controlled workspace expectations
- validate that `FOCUS_VALIDATION_POLICY_GATE` and `ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES` are treated as expected strategy gates, not hard failures
- assert that execution-system suite remains green while policy-gate wording remains explicit

## First later-multi-wave design cut

The first later-multi-wave design cut should stay narrower than a real multi-wave implementation.

Minimal scope:
- define how a roadmap activity would represent at least two waves in `ACTIVE.md`
- define how `ready_slices`, `inflight_slices`, `blocked_slices`, and `integration_step` should evolve across a wave boundary
- define the minimum invariant set required before a future multi-wave test or runner change is allowed
- define what must remain identical between single-wave and later multi-wave closeout semantics

Minimum invariant set for the first later-multi-wave design cut:
- only one focus activity remains runtime truth at any moment, even when multiple waves exist
- each slice may appear in exactly one of `ready_slices`, `inflight_slices`, or `blocked_slices` at a time
- advancing from wave `Wn` to `Wn+1` requires `integration_step` for `Wn` to be recorded before new `ready_slices` are exposed
- `blocked_slices` in `Wn` may move to `ready_slices` in `Wn+1` only when their declared dependency boundary is satisfied
- `last_wave_result` must summarize what changed at the previous boundary rather than duplicate the whole wave state
- closeout semantics must still derive from the current focus activity, current slice, validation state, and last committed execution truth rather than from historical chat reconstruction

Explicit non-goals:
- do not implement multi-wave runner logic in this cut
- do not mutate product repo runtime behavior
- do not introduce background agent orchestration requirements
- do not attempt exhaustive coverage of every possible wave transition
- do not weaken the current single-wave guarantees just to make future multi-wave wording easier

Go / no-go rule for a later implementation wave:
- `go` only if the design cut stays workspace-local, leaves runtime behavior unchanged, and produces a small invariant set that can be tested without broad fixture churn
- `no-go` if the design still depends on speculative orchestration, unstable runtime semantics, or would force `ACTIVE.md` to carry excessive live state

Current recommendation after `DX-E.E8` design discovery:
- `no-go` for immediate multi-wave implementation

Rationale:
- the current system now has strong single-wave coverage, but no evidence yet that a broader multi-wave implementation would add enough confidence to offset the added state complexity
- the invariants are now explicit, which is the right stopping point for this cut
- a future implementation wave should wait until a concrete multi-wave need appears that cannot be satisfied by the current single-wave model plus governance checks

## Success criteria

The upgrade is successful when:
- complex work is decomposed through a repeatable intake path
- slices are structurally checkable rather than merely descriptive
- parallel waves are explicit and safely bounded
- runtime wave state is recoverable from `ACTIVE.md`
- validation and closeout reflect integrated wave execution rather than only final outcomes
- the system remains additive, understandable, and compatible with focus-first execution
