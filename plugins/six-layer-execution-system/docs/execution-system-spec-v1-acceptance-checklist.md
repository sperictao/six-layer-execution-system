# execution-system-spec-v1 acceptance checklist

## Purpose

This checklist is the document-form acceptance baseline for `execution-system-spec-v1`.

It answers one question:

Has the execution system reached a state where the core v1 model is materially implemented,
validated, and safe to treat as maintenance-mode unless a concrete reopen trigger appears?

---

## Acceptance result format

Use these result labels when reviewing:
- `pass` - implemented and validated in the current workspace
- `partial` - present but not yet fully formalized
- `fail` - missing or contradicted by current workspace state
- `n/a` - intentionally out of scope for this acceptance wave

---

## 1. Layer model

### 1.1 Six-layer structure exists
- [ ] `pass` `contract` layer exists and is used for long-lived constraints
- [ ] `pass` `roadmap` layer exists and is used for phase structure
- [ ] `pass` `tasks` layer exists and is used for slice design
- [ ] `pass` `ACTIVE` exists as runtime truth
- [ ] `pass` `decisions` exists for durable rationale
- [ ] `pass` `memory` exists for historical/recovery notes

Evidence:
- `contracts/execution-system-contract.md`
- `roadmaps/execution-system-spec-v1-roadmap.md`
- `tasks/execution-system-spec-v1-tasks.md`
- `ACTIVE.md`
- `decisions/`
- `memory/`

### 1.2 Single-layer single-truth boundaries are documented
- [ ] `pass` spec states that each layer owns one class of truth
- [ ] `pass` spec forbids reconstructing runtime truth from roadmap/tasks/memory

Evidence:
- `docs/execution-system-spec-v1.md`

---

## 2. ACTIVE as runtime truth

### 2.1 ACTIVE is the only runtime truth source
- [ ] `pass` progress / current-state questions resolve through `ACTIVE.md`
- [ ] `pass` repo-backed fact checks are treated as verification, not alternate truth

Evidence:
- `ACTIVE.md`
- `docs/execution-system-spec-v1.md`

### 2.2 Focus-first execution is real
- [ ] `pass` only the current focus activity is treated as the default runnable activity
- [ ] `pass` non-focus activities are not auto-advanced

Evidence:
- `ACTIVE.md`
- `scripts/validate_focus_first.py`
- `docs/active-ledger-v2.md`

### 2.3 ACTIVE has been slimmed toward runtime-only content
- [ ] `pass` execution-system roadmap card keeps concise recovery pointers instead of a long milestone diary
- [ ] `partial` not every activity card has necessarily had a second slimming pass yet

Evidence:
- `ACTIVE.md`
- `docs/execution-system-spec-v1.md`

---

## 3. Activity schema

### 3.1 Activity types are formalized
- [ ] `pass` roadmap activity schema is defined in spec and used in practice
- [ ] `pass` waiting activity schema is defined in spec and used in practice
- [ ] `pass` simple activity schema is defined in spec and used in practice

Evidence:
- `docs/execution-system-spec-v1.md`
- `ACTIVE.md`

### 3.2 Focus-first policy and strategy-gate semantics are aligned
- [ ] `pass` `validate_focus_first.py` distinguishes `OK`, `POLICY_GATE`, and `FAILED`
- [ ] `pass` acceptance treats a policy gate as `OK_WITH_POLICY_GATES`, not as a broken model

Evidence:
- `scripts/validate_focus_first.py`
- `scripts/accept_active_ledger_v2.py`
- `docs/active-ledger-v2.md`

---

## 4. Task and roadmap structure

### 4.1 Roadmap owns phase truth, not runtime truth
- [ ] `pass` roadmap files keep phase objective / dependencies / outputs / exit criteria / risks
- [ ] `pass` roadmap does not act as the live current-state source

Evidence:
- `roadmaps/execution-system-spec-v1-roadmap.md`
- `roadmaps/execution-system-testing-roadmap.md`

### 4.2 Tasks own slice design
- [ ] `pass` migrated task slices use `phase_id`
- [ ] `pass` migrated task slices use `rollback_strategy`
- [ ] `pass` task checker exists and validates migrated slices only

Evidence:
- `tasks/execution-system-spec-v1-tasks.md`
- `tasks/execution-system-testing-tasks.md`
- `tasks/active-ledger-v2-tasks.md`
- `scripts/check_task_slice_schema.py`

---

## 5. Completion protocol and state machine

### 5.1 Completion is treated as protocol, not vibe
- [ ] `pass` spec defines completion as more than code landed
- [ ] `pass` closeout artifact is part of completion semantics
- [ ] `pass` handoff payload derivation is part of completion semantics

Evidence:
- `docs/execution-system-spec-v1.md`
- `scripts/complete_slice.py`
- `scripts/create_slice_closeout.py`

### 5.2 `closed_out` is encoded in artifact semantics
- [ ] `pass` closeout artifact writes `slice_state: closed_out`
- [ ] `pass` verifier rejects missing or invalid `slice_state`

Evidence:
- `scripts/create_slice_closeout.py`
- `scripts/check_slice_closeout.py`
- `tests/test_slice_closeout_state.py`

### 5.3 `validated` is encoded in artifact semantics
- [ ] `pass` closeout artifact writes `validation_state: validated`
- [ ] `pass` verifier rejects missing or invalid `validation_state`

Evidence:
- `scripts/create_slice_closeout.py`
- `scripts/check_slice_closeout.py`
- `tests/test_slice_closeout_state.py`

### 5.3a Current focus identity is explicit in closeout surfaces
- [ ] `pass` closeout artifact writes `current_focus_activity_id`
- [ ] `pass` canonical payload surface includes `current_focus_activity_id`
- [ ] `pass` path coverage verifies artifact -> payload all preserve `current_focus_activity_id`

Evidence:
- `scripts/create_slice_closeout.py`
- `scripts/build_slice_handoff.py`
- `tests/test_execution_system_path_closeout_payload_identity.py`

### 5.4 Full slice state machine is only partially formalized
- [ ] `partial` `validated` and `closed_out` are now explicit in artifacts
- [ ] `partial` earlier states such as `planned`, `in_progress`, and `implemented` are still more documented than fully enforced in runtime/task data

Interpretation:
- this is no longer a foundational gap
- it is still a fair future refinement area if repeated operator pain appears

---

## 6. Checker and workflow implementation

### 6.1 Hard-fail checker wave exists
- [ ] `pass` ACTIVE field checker exists
- [ ] `pass` generated decomposition consistency checker exists
- [ ] `pass` migrated task slice schema checker exists
- [ ] `pass` task dependency graph checker exists
- [ ] `pass` parallel safety checker exists
- [ ] `pass` hard-fail checkers have smoke coverage

Evidence:
- `scripts/check_active_consistency.py`
- `tests/test_check_active_consistency.py`
- `scripts/check_generated_decomposition_consistency.py`
- `tests/test_check_generated_decomposition_consistency.py`
- `scripts/check_task_slice_schema.py`
- `tests/test_check_task_slice_schema.py`
- `scripts/check_task_dependency_graph.py`
- `tests/test_check_task_dependency_graph.py`
- `scripts/check_parallel_safety.py`
- `tests/test_check_parallel_safety.py`

### 6.1a Active wave-state checker is promoted into the unified hard-fail runner
- [ ] `pass` `check_active_wave_state.py` exists
- [ ] `pass` active wave-state smoke coverage exists
- [ ] `pass` active wave-state checker is included in `run_execution_system_checks.py`
- [ ] `pass` runner summary has a recovery hint for active wave-state failures

Evidence:
- `scripts/check_active_wave_state.py`
- `tests/test_check_active_wave_state.py`
- `scripts/run_execution_system_checks.py`
- `tests/test_run_execution_system_checks.py`
- `ACTIVE.md`

### 6.2 Advisory wave exists without silently becoming hard-fail
- [ ] `pass` oversized migration slice advisory exists
- [ ] `pass` advisory remains non-blocking
- [ ] `pass` advisory has smoke coverage

Evidence:
- `scripts/check_oversized_migration_slices.py`
- `tests/test_check_oversized_migration_slices.py`
- `scripts/run_execution_system_checks.py`

### 6.3 Unified workflow runner exists
- [ ] `pass` a single runner executes the current checker suite
- [ ] `pass` raw output is preserved
- [ ] `pass` summary footer is appended, not substituted
- [ ] `pass` summary footer has smoke coverage

Evidence:
- `scripts/run_execution_system_checks.py`
- `tests/test_run_execution_system_checks.py`

### 6.4 Workflow adoption exists
- [ ] `pass` closeout-oriented flow reuses the unified runner
- [ ] `pass` acceptance-oriented flow reuses the unified runner

Evidence:
- `scripts/complete_slice.py`
- `scripts/accept_active_ledger_v2.py`

---

## 7. Decisions and contract landing

### 7.1 Contract layer is real, not theoretical
- [ ] `pass` execution-system has a dedicated contract file
- [ ] `pass` contract contains stable constraints rather than current runtime state

Evidence:
- `contracts/execution-system-contract.md`

### 7.2 Decision layer is real, not theoretical
- [ ] `pass` runtime / execution-system decisions exist as durable records
- [ ] `pass` execution-system strategic decisions exist as durable records

Evidence:
- `decisions/runtime/`
- `decisions/README.md`

---

## 8. Operational maintenance posture

### 8.1 Execution-system line is no longer default infinite backlog
- [ ] `pass` post-alignment audit conclusion is documented
- [ ] `pass` maintenance mode is documented
- [ ] `pass` explicit reopen conditions are documented
- [ ] `pass` explicit re-entry protocol is documented
- [ ] `pass` resume-style trigger rule is documented
- [ ] `pass` task-status / task-resume replies may not rely on conversational memory alone when `ACTIVE.md` exists as execution truth

Evidence:
- `docs/execution-system-spec-v1.md`
- `roadmaps/execution-system-spec-v1-roadmap.md`
- `tasks/execution-system-spec-v1-tasks.md`
- `ACTIVE.md`
- `skills/six-layer-execution-system/SKILL.md`

### 8.2 Runtime state reflects maintenance posture
- [ ] `pass` `execution-system-spec-v1` is parked / non-autopilot
- [ ] `pass` default review focus has been handed back to `waiting-ledger-review`
- [ ] `pass` focus-first validation is green under a non-execution-system maintenance focus

Evidence:
- `ACTIVE.md`
- `scripts/validate_focus_first.py`
- `scripts/accept_active_ledger_v2.py`

### 8.3 Resume-style triggers use the same recovery model
- [ ] `pass` resume-style triggers explicitly follow the same recovery sequence as manual `go` / `continue` / `继续` style prompts
- [ ] `pass` resume-style triggers do not infer task state from chat memory alone when `ACTIVE.md` is the declared execution truth
- [ ] `pass` resume-style trigger planning uses the same parallel-dispatch rule as ordinary execution inside the current focus activity
- [ ] `pass` resume-style trigger planning keeps hard dependency chains and write-conflicting work serial rather than forcing unsafe parallelism

Evidence:
- `skills/six-layer-execution-system/SKILL.md`
- `docs/execution-system-spec-v1.md`

---

## 9. Recommended acceptance command set

Run the following as the practical acceptance bundle:

- run these commands from the repository root
- the `tests/` commands are repo-local development checks and require the
  source checkout plus the explicit `PYTHONPATH` prefix
- a standalone plugin copy only guarantees `accept_active_ledger_v2.py` and
  `run_execution_system_checks.py`; repo-local smoke tests are intentionally
  outside that distribution boundary

```bash
python3 scripts/accept_active_ledger_v2.py
python3 scripts/run_execution_system_checks.py
PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts" python3 tests/test_slice_closeout_state.py
PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts" python3 tests/test_run_execution_system_checks.py
PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts" python3 tests/test_check_oversized_migration_slices.py
PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts" python3 tests/test_check_task_slice_schema.py
PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts" python3 tests/test_check_active_consistency.py
```

Expected interpretation:
- all commands should pass
- `run_execution_system_checks.py` may still print advisory output
- advisory output is expected and should not be treated as hard-fail
- `accept_active_ledger_v2.py` should be fully green under a valid non-execution-system focus

---

## 10. Final acceptance call

### Final call
- [x] `pass` core v1 alignment is substantially landed
- [x] `pass` execution-system line is safe to treat as maintenance-mode by default
- [x] `pass` future execution-system work should reopen only via explicit trigger
- [ ] `partial` some incremental cleanup/polish opportunities still remain

### Meaning of this result
This checklist does **not** claim that no future improvement is possible.
It means the system has crossed the threshold where remaining work is no longer a foundational correctness blocker for v1.

In practical terms:
- the final model is implemented enough to trust
- the runtime truth model is stable enough to operate from
- the checker / advisory / closeout / acceptance loop is real
- further work should be justified by concrete pain, not by open-ended system polish
