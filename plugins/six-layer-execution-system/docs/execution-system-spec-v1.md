# Execution System Spec v1

## 1. Purpose

This spec defines how complex work is represented, executed, resumed, validated, and closed out in this workspace.

The system exists to solve six problems:
- keep long-running work from drifting
- prevent multiple files from competing as the current truth
- allow multiple activities to coexist without cross-running
- make progress replies reproducible
- define what “completed” really means
- make resume / recovery cheap after session resets or compaction

The core principle is:

**layered truth, focus-first execution, explicit completion protocol.**

---

## 2. System layers

The execution system uses six layers.

### 2.1 Contract layer
Owns long-lived project constraints and execution invariants.

Examples:
- invariants
- non-goals
- forbidden moves
- allowed tradeoffs
- validation baseline
- completion philosophy

### 2.2 Roadmap layer
Owns phase order, milestones, dependencies, exit criteria, and phase risks.

### 2.3 Tasks layer
Owns PR queue, slices, per-slice validation, done definitions, and rollback strategy.

### 2.4 ACTIVE layer
Owns the only runtime truth about what is currently being executed.

### 2.5 Decisions layer
Owns durable “why” records when important choices or tradeoffs are made.

### 2.6 Memory layer
Owns daily logs, historical notes, and recovery aids.
It is not execution truth.

### 2.7 Demand Intake step
Demand Intake is an upstream decomposition step for complex work.
It is not a seventh runtime-truth layer.

Its job is to normalize a complex request before it is expanded into:
- `contract`
- `roadmap`
- `tasks`
- `ACTIVE`

Demand Intake should answer:
- what kind of work this is
- what outcome is desired
- what constraints and non-goals apply
- what dependency shape is already visible
- what can likely run in parallel vs what must remain serial
- what outputs and validation are expected

---

## 3. Single-source-of-truth rules

### 3.1 One layer, one truth
Each layer may own only one class of truth.

- `contract` -> long-term constraints
- `roadmap` -> phase / milestone structure
- `tasks` -> slice design
- `ACTIVE` -> current execution state
- `decisions` -> durable rationale
- `memory` -> history and recovery context

### 3.2 Forbidden duplication
Do not duplicate the same layer of truth across multiple files.

Examples:
- do not store current slice in roadmap
- do not store long-term invariants only in ACTIVE notes
- do not reconstruct current runtime state from memory logs
- do not use daily notes as the current source of truth

### 3.3 Runtime questions always resolve through ACTIVE
For questions like:
- what are we doing now?
- what is blocked?
- what is next?
- what was the last verified slice?

The answer must come from:
- `ACTIVE.md`
- plus repo / validation fact checks when repo-backed

---

## 4. Focus-first execution model

### 4.1 Multi-activity is allowed
The workspace may track multiple activities at the same time.

### 4.2 Only the current focus activity may run by default
The default rule is:
- only `current_focus_activity_id` may enter autonomous execution
- non-focus activities may exist for tracking, recovery, reminders, or future switching
- non-focus activities must not be auto-advanced silently

### 4.3 Focus switching must be explicit
Changing active execution requires an explicit focus switch, not an implicit jump.

### 4.4 Parallel-first execution inside the focus activity
Within the current focus activity, execution should default to parallel-first planning when the work can be split safely.

Required planning sequence:
1. identify the dependency graph
2. separate parallelizable nodes from true serial dependencies
3. batch independent read-only or non-conflicting tasks into the same execution wave
4. wait for the whole wave to finish
5. integrate the results into a single stage output
6. repeat until the slice is complete

Parallel execution is allowed only when:
- sub-tasks do not write the same file or mutate the same runtime state
- each sub-task has a clear input boundary and expected output
- the integration step is explicitly owned by the parent execution path

Prefer serial execution when:
- work forms a hard dependency chain such as `A -> B -> C`
- two tasks would touch overlapping regions of the same file
- later choices depend on facts produced by earlier implementation steps

Parallelism is an execution tactic, not a reason to violate focus-first. Only the current focus activity may be parallelized by default.

---

## 5. File responsibilities

## 5.0 Demand Intake cards
Recommended path:
- `demands/<date>-<topic>.md`

Demand Intake cards are recommended for complex work before contract / roadmap / tasks are written or expanded.

Required fields:
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

Allowed `task_type` values:
- `implementation`
- `refactor`
- `governance`
- `testing`
- `docs`
- `coordination`
- `simple`

Demand Intake cards must not contain:
- current live wave state
- inflight slice state
- notification state
- alternate runtime truth that competes with `ACTIVE.md`

## 5.1 Contract files
Recommended path:
- `contracts/<project>-contract.md`

Contract files contain:
- goal
- scope
- invariants
- non-goals
- forbidden moves
- allowed tradeoffs
- validation baseline
- completion philosophy
- review triggers

Contract files may also contain a `Decomposition Guardrails` section for complex work.

Recommended guardrail fields:
- `allowed_slice_shapes`
- `forbidden_slice_shapes`
- `preferred_dependency_shape`
- `parallelism_policy`
- `integration_constraints`
- `review_triggers`

Guardrail intent:
- define what kinds of slice shapes are allowed
- define what kinds of multi-layer changes are forbidden in one slice
- define when parallel execution is acceptable vs unsafe
- define what must be re-validated when multiple slice outputs are integrated

Contract files must not contain:
- current phase
- current slice
- current commit
- notification state
- daily progress

## 5.2 Roadmap files
Recommended path:
- `roadmaps/<project>-roadmap.md`

Roadmap files contain:
- goal
- contract reference
- validation baseline
- phases
- per-phase objective / dependencies / outputs / exit criteria / risks
- current recommended phase

Roadmap files may also define phase-level decomposition guidance.

Recommended per-phase guidance fields:
- `decomposition_strategy`
- `recommended_wave_shape`

Guidance intent:
- `decomposition_strategy` describes how a phase should be sliced
- `recommended_wave_shape` describes whether a phase is best executed as `serial`, `parallel-wave`, or `mixed`
- roadmap may express phase dependency shape and wave guidance, but not live wave state

Roadmap files must not contain:
- current live slice state
- recent commit logs
- notification status
- execution diary

## 5.3 Tasks files
Recommended path:
- `tasks/<project>-tasks.md`

Tasks files contain:
- current phase reference
- PR queue
- per-slice goal
- phase id
- scope
- target files
- dependencies
- validation
- done definition
- rollback strategy
- risk

Tasks files may also define executable slice-DAG metadata.

Recommended per-slice DAG fields:
- `depends_on`
- `parallel_safe`
- `shared_write_targets`
- `expected_artifacts`
- `integration_notes`
- `handoff_output`

DAG intent:
- `depends_on` expresses upstream slice ids
- `parallel_safe` declares whether the slice may run in the same wave as other independent slices
- `shared_write_targets` makes same-wave conflicts visible
- `expected_artifacts` defines what outputs should exist when a slice is done
- `integration_notes` defines how the parent execution path should merge the slice output
- `handoff_output` defines the expected return shape for completion

Tasks files must not contain:
- live focus activity selection
- notification inflight state
- daily recovery notes

## 5.4 ACTIVE
`ACTIVE.md` is the only runtime truth.

Recommended contents:
- ledger meta
- minimal runtime rules
- activity index
- activity cards
- operational pointers

Roadmap activities in `ACTIVE.md` may also define minimal wave-state fields when execution uses a parallel-wave model.

Recommended roadmap wave-state fields:
- `execution_mode`
- `current_wave_id`
- `ready_slices`
- `inflight_slices`
- `blocked_slices`
- `integration_step`
- `last_wave_result`

Wave-state intent:
- `execution_mode` declares whether the current activity is running as `serial` or `parallel-wave`
- `current_wave_id` identifies the active execution wave
- `ready_slices` lists slices that may run now
- `inflight_slices` lists slices currently being executed
- `blocked_slices` lists slices waiting on dependencies
- `integration_step` defines how the parent execution path should merge the current wave output
- `last_wave_result` gives a concise summary of the previous wave outcome

ACTIVE should avoid becoming:
- a narrative history file
- a general-purpose documentation dump
- a duplicate roadmap
- a duplicate decision log

### 5.4.1 Second-pass slimming boundary
A second-pass ACTIVE slimming should preserve only runtime-recovery-critical fields.

Keep in ACTIVE when the field directly answers one of these questions:
- what is the current focus activity
- what slice is live now
- what validation command or repo fact should be checked next
- what is the most recent durable execution artifact needed for recovery
- what blocker currently prevents progress

Move out of ACTIVE when the content is mainly:
- a long chronological changelog
- a dense backlog of past milestones already reflected in docs or git history
- rationale better stored as a decision record
- explanation of policy that already exists in spec/docs

For roadmap activities, this generally means:
- keep concise `last_artifact` pointers that help recovery
- keep concise `last_decision` pointers that help explain the current path
- avoid letting either field become a running narrative of every historical step

## 5.5 Decisions
Recommended path:
- `decisions/<project>/YYYY-MM-DD-<topic>.md`

Use for:
- high-impact design choices
- rejected alternatives
- risky tradeoffs
- changes to contract / completion / notification semantics

## 5.6 Memory
Recommended paths:
- `memory/YYYY-MM-DD.md`
- `memory/working-buffer.md`

Use for:
- daily notes
- raw observations
- session-recovery breadcrumbs
- temporary exchange logs

Do not use memory as the current execution truth.

---

## 6. Activity type system

Activities in `ACTIVE.md` are typed.

### 6.1 roadmap activity
Required fields:
- `activity_id`
- `title`
- `type: roadmap`
- `status`
- `priority`
- `autopilot`
- `path` or `repo + path`
- `roadmap_doc`
- `tasks_doc`
- `current_slice_id`
- `next_step`
- `validation`
- `last_artifact`
- `last_decision`

Recommended fields:
- `next_slice_id`
- `blocked_by`
- `last_commit`
- `retrieval_keys`
- `query_recipe`
- `done_when`
- `execution_mode`
- `current_wave_id`
- `ready_slices`
- `inflight_slices`
- `blocked_slices`
- `integration_step`
- `last_wave_result`

Forbidden fields:
- `waiting_on`
- `unblock_condition`

### 6.2 waiting activity
Required fields:
- `activity_id`
- `title`
- `type: waiting`
- `status: blocked|parked`
- `autopilot: false`
- `waiting_on`
- `unblock_condition`
- `next_step`
- `validation`

Forbidden fields:
- `current_slice_id`
- `last_commit`
- `roadmap_doc`
- `tasks_doc`

### 6.3 simple activity
Required fields:
- `activity_id`
- `title`
- `type: simple`
- `status`
- `autopilot`
- `goal`
- `scope`
- `next_step`
- `validation`
- `done_definition`

Forbidden fields:
- `current_slice_id`
- `last_commit`
- `roadmap_doc`
- `tasks_doc`

---

## 7. Status model

### 7.1 Activity statuses
Allowed activity status values:
- `ready`
- `in_progress`
- `blocked`
- `parked`
- `done`

Definitions:
- `ready` -> clearly defined and safe to begin
- `in_progress` -> actively being worked on
- `blocked` -> cannot proceed until something external changes
- `parked` -> intentionally paused, not necessarily blocked
- `done` -> completed and verified at the activity level

### 7.2 Slice completion state machine
Roadmap slices should be evaluated with the following state model:
- `planned`
- `in_progress`
- `implemented`
- `validated`
- `closed_out`

Definitions:
- `planned` -> slice exists but work has not started
- `in_progress` -> code / docs / structure are actively changing
- `implemented` -> changes landed but full validation not yet complete
- `validated` -> required validation passed and should be representable explicitly in closeout-adjacent artifact semantics
- `closed_out` -> validation passed, commit recorded, ACTIVE advanced atomically, closeout artifact frozen with `validation_state: validated`, `slice_state: closed_out`, and explicit `current_focus_activity_id`, notification state traceable

Rule:
**Only `closed_out` slices may be announced externally as complete.**

---

## 8. Completion protocol

A roadmap slice is considered complete only when all of the following are true:

1. code / change landed
2. validation passed
3. commit recorded
4. `ACTIVE.md` switched to next slice atomically
5. closeout artifact created and explicitly marked `validation_state: validated` plus `slice_state: closed_out`, with explicit `current_focus_activity_id`
6. notification state is traceable (`pending`, `inflight`, or `sent`)

This is the workspace-wide completion contract.

### 8.1 Notification publication rule
Completion notifications must be generated from the frozen closeout artifact, not from live ACTIVE fields.
The canonical payload surface must explicitly include `current_focus_activity_id` from that frozen artifact.

### 8.2 Phase completion rule
A roadmap phase is complete only when:
- all required slices for that phase are complete
- roadmap exit criteria for that phase are satisfied

---

## 9. Recovery protocol

When resuming after a reset / compaction / interruption:

1. read `ACTIVE.md`
2. identify `current_focus_activity_id`
3. read that activity card first
4. if it is a roadmap activity, read linked roadmap/tasks docs
5. read contract if long-term constraints matter
6. consult recent memory / decisions only after runtime truth is loaded
7. verify repo-backed facts against git / files / validation outputs before answering progress questions

### 9.1 Resume-style trigger rule
Short imperative or resume-like user messages must be treated as execution recovery, not general chat.

Operational prompt-rule source:
- `skills/six-layer-execution-system/SKILL.md` is the single prompt-rule source of truth for resume handling, heartbeat/manual alignment, notification levels, behavior boundaries, and tool entrypoints
- `ACTIVE.md` remains runtime truth and must not be replaced by prompt prose

Examples:
- `go`
- `continue`
- `继续`
- `resume`
- `next`
- `start`
- `where were we`
- `what were we doing`

Required recovery sequence:
1. read `memory/working-buffer.md` first when it exists
2. read `ACTIVE.md`
3. resolve `current_focus_activity_id`
4. read the focus activity card
5. if it is a roadmap activity, read its linked roadmap/tasks docs
6. inspect repo/workspace facts before replying or acting

Forbidden recovery shortcuts:
- do not infer current state from old memory notes alone
- do not assume roadmap == current state
- do not auto-run a non-focus activity
- do not answer task-status or task-resume questions from conversational memory alone when `ACTIVE.md` exists as execution truth

---

## 10. Progress reply protocol

For progress questions, answer in this order:
- current focus activity
- current slice / stage
- most recent completed slice / artifact
- validation state
- blocker state
- next step

Do not answer progress from memory alone when repo-backed facts can be checked.

---

## 11. Templates and adoption

The canonical starter templates for this spec live in:
- `references/templates.md`

Recommended rollout pattern:
1. define / update contract
2. keep roadmap phase-only
3. keep tasks slice-oriented
4. keep ACTIVE runtime-only
5. use decisions for major rationale shifts
6. use memory only for logs and recovery breadcrumbs

### 11.1 Decisions adoption guidance
Use `decisions/` when one of the following is true:
- a long-lived constraint is chosen or revised
- multiple plausible options were considered
- a risky tradeoff is intentionally accepted
- future-you would otherwise forget *why* this path was chosen

Do not backfill every historical conversation.
Start with a few high-signal decisions that explain the system’s current shape.

---

## 12. Validation and migration policy

### 12.1 What belongs in docs vs checkers
Use docs/specs for:
- layer boundaries
- naming conventions
- adoption guidance
- examples and templates
- migration sequencing heuristics

Use checkers/workflows for:
- required ACTIVE fields
- focus activity resolution
- repo/commit drift detection
- closeout integrity checks
- runnable activity filtering

Rule:
- if a rule must fail loudly during execution, it should eventually live in a checker or workflow
- if a rule mainly explains intent, structure, or adoption, it may remain in docs

### 12.2 Migration policy
Migration should follow this order:
1. land spec + templates
2. land contract for the target project
3. tighten roadmap to phase-only truth
4. tighten tasks to phase/slice/rollback structure
5. slim ACTIVE without losing runtime truth
6. add high-signal decisions
7. only then consider new checker/workflow enforcement

### 12.2.1 Enforcement backlog candidates
The next likely automation candidates are:

#### ACTIVE-focused candidates
- require focus roadmap activities to carry `source_doc`, `roadmap_doc`, `tasks_doc`, and `last_commit`
- detect repo HEAD drift against `last_commit`
- warn when a roadmap activity stays on a broad slice after repeated heterogeneous progress

#### Roadmap-focused candidates
- warn when roadmap `Current recommended phase` visibly lags behind ACTIVE focus progress
- flag roadmap files that still embed live runtime-like wording after a project claims migration

#### Tasks-focused candidates
- require `phase_id` on roadmap-aligned slices in migrated task docs
- require `rollback_strategy` on migrated slices and PR groups
- flag oversized migration slices that span multiple distinct subgoals without sub-slice IDs

#### Decisions-focused candidates
- validate decisions index / examples exist once a project claims decision-layer adoption
- warn when a project claims durable rationale adoption but has no high-signal decision records

These are candidates, not all immediate requirements.

### 12.2.2 First automation candidates
The first likely checker/workflow candidates should stay intentionally small:

1. `ACTIVE` focus roadmap activities must carry:
   - `source_doc`
   - `roadmap_doc`
   - `tasks_doc`
   - `last_commit`
2. migrated roadmap-aligned task slices should carry:
   - `phase_id`
   - `rollback_strategy`
3. warn when a migration slice is visibly too broad and repeated progress is being logged against one opaque slice id

These are preferred first candidates because:
- they are structurally deterministic
- they have relatively low false-positive cost
- they already match current migration experience in this workspace

The following should wait until later:
- nuanced wording checks in roadmap prose
- any rule that requires fuzzy interpretation of “enough migration”
- aggressive enforcement on partially migrated legacy task docs

### 12.2.3 First checker/workflow design backlog
The first design backlog should likely include:

1. **ACTIVE roadmap activity field checker**
   - verifies `source_doc`, `roadmap_doc`, `tasks_doc`, `last_commit`
   - fails loudly because these are deterministic runtime fields

2. **Migrated task slice schema checker**
   - verifies `phase_id` + `rollback_strategy` for slices that already claim migrated structure
   - should avoid touching obviously legacy sections that are not yet migrated

3. **Oversized migration slice warning**
   - warns when repeated heterogeneous progress accumulates under one opaque slice id
   - should likely be advisory first, not hard-fail

A good design backlog item should specify:
- target rule
- input files
- deterministic trigger
- error / warning mode
- safe recovery path

### 12.2.4 First implementation wave
Recommended order for the first implementation wave:

1. **ACTIVE roadmap activity field checker**
   - first because it is deterministic and already matches current consistency expectations

2. **Migrated task slice schema checker**
   - second because migration coverage is now meaningful, but still partial
   - should be scoped only to clearly migrated sections

3. **Oversized migration slice warning**
   - third because it is useful, but should begin as advisory until enough examples exist

Defer for later:
- roadmap prose style checks
- fuzzy migration-completeness scoring
- aggressive enforcement on mixed legacy/migrated task docs

### 12.2.5 First implementation-prep slice
The first implementation-prep slice should target the **ACTIVE roadmap activity field checker**.

It should define:
- exact required fields to enforce for focus roadmap activities
- which missing fields are hard errors vs future candidates
- how failures are rendered for human recovery
- how to avoid overfitting to one project-specific activity shape

### 12.2.6 Exact contract for the first checker
The first checker should initially hard-fail only on deterministic focus roadmap requirements.

#### Hard-fail fields
The focus roadmap activity must provide:
- `source_doc`
- `roadmap_doc`
- `tasks_doc`
- `current_slice_id`
- `next_slice_id`
- `last_commit`
- non-empty `next_step`
- non-empty `validation`
- non-empty `blocked_by`

For the three doc pointer fields (`source_doc`, `roadmap_doc`, `tasks_doc`), the first checker wave should also require that the referenced file actually exists.

These fields are hard-fail because they answer the minimum execution questions directly:
- what spec/contract defines the work
- what roadmap/tasks docs shape the work
- what slice is live now
- what slice comes next
- what commit anchors repo-backed progress
- what the operator should do next
- how the operator validates recovery or completion
- whether the activity is actually blocked

#### Drift checks
The checker should also keep the existing repo-backed drift behavior:
- verify `last_commit` resolves in the repo
- verify repo `HEAD` matches `last_commit` for the current focus roadmap activity

#### Current validation entrypoint
The current Phase 6 checker suite can be run together via:
- `python3 scripts/run_execution_system_checks.py`

Current workflow adoption:
- `scripts/accept_active_ledger_v2.py` now reuses this suite instead of calling the ACTIVE checker directly
- `scripts/complete_slice.sh prepare` now uses this suite before creating closeout artifacts
- the unified runner now also prints advisory-only outputs such as oversized migration slice warnings, while keeping hard-fail exit semantics unchanged

Operational rule of thumb:
- use `python3 scripts/run_execution_system_checks.py` for routine checker validation
- use `python3 scripts/check_active_consistency.py` when you only need the ACTIVE runtime truth check or are repairing `ACTIVE.md`
- use `python3 scripts/check_task_slice_schema.py` when you are iterating specifically on migrated task-doc structure

Note:
- `accept_active_ledger_v2.py` may still fail on its separate `focus-first` gate when the current focus activity is intentionally `autopilot: false`; this does not mean the unified checker suite adoption is broken.

#### Defer for later waves
The first checker should explicitly defer all of the following:
- optional roadmap activity metadata such as `objective`, `done_when`, `notify_on`, `notify_suppression_window`, `last_validation`, or richer retrieval aids
- roadmap prose checks such as whether `Current recommended phase` wording is ideal
- tasks migration coverage checks beyond deterministic schema rules already scoped into later work
- decisions adoption checks
- any heuristic that tries to score whether a project is "migrated enough"
- any fuzzy interpretation of whether `next_step` or `blocked_by` is semantically good rather than merely present and non-empty

#### Failure rendering and recovery path
Failures must stay human-readable and immediately recoverable.

The checker output should:
- report each failure as `scope: message`
- use the focus activity id in scope when possible
- name the exact missing, empty, drifting, or broken-reference field
- avoid dumping unrelated policy prose
- preserve the operator's recovery path in one pass

For missing field failures, the operator should be able to recover by:
1. opening `ACTIVE.md`
2. locating the focus activity card
3. adding or repairing the named field
4. rerunning `python3 scripts/check_active_consistency.py`

For repo drift failures, the operator should be able to recover by:
1. checking the focus repo `HEAD`
2. deciding whether `ACTIVE.md:last_commit` is stale or the repo moved unexpectedly
3. repairing the intended source of truth
4. rerunning the checker

If the focus repo is the workspace repo itself and only `ACTIVE.md` is dirty, the checker may emit a more specific self-drift hint so the operator can distinguish "I just updated the ledger" from a broader unexpected repo move.

Non-goals for the first checker wave:
- do not enforce project-specific optional fields
- do not parse roadmap prose quality
- do not enforce decisions adoption
- do not infer whether a task doc is fully migrated enough beyond explicit deterministic structure
- do not turn advisory migration heuristics into hard failures

### 12.2.7 Exact contract for the second checker
The second checker should target migrated task slice schema only, not all task prose.

#### Hard-fail scope
The checker should evaluate only slices that already clearly claim migrated structure.

A slice counts as in-scope when it is part of a roadmap-aligned task section and already includes at least one of:
- `phase_id`
- `rollback_strategy`
- an explicit slice heading under a PR queue section that is already being maintained in the migrated template style

#### Hard-fail requirements
For in-scope migrated slices, the checker should require:
- `phase_id`
- `rollback_strategy`

It may also require that:
- the slice has a heading / identifier
- the required fields are non-empty

#### Explicit non-goals
The second checker should not:
- rewrite or reinterpret legacy task sections
- force migration of untouched historical slices
- infer semantic quality of `goal`, `scope`, or `risk`
- require every PR group in every old task doc to match the new template immediately
- hard-fail on mixed legacy/migrated documents as long as the migrated slices themselves are structurally sound

#### Failure rendering and recovery path
The output should stay deterministic and local:
- report `scope: message`
- include enough task-doc context to identify the broken slice quickly
- name the missing structural field directly
- avoid broader commentary about migration philosophy

Recovery should be one pass:
1. open the named task doc
2. locate the named slice or nearest migrated slice block
3. add the missing structural field
4. rerun the checker

#### Adoption gate
This checker should remain scoped to clearly migrated slices until the execution-system-owned samples demonstrate that migrated slices can coexist safely with legacy sections.

#### Current reference samples
Use a controlled pair of in-repo execution-system samples for this checker design:
- `tasks/execution-system-testing-tasks.md` supplies clearly migrated slices with stable `phase_id` and `rollback_strategy` usage
- `tasks/active-ledger-v2-tasks.md` preserves older `Task A1` / `Task A2` style headings that should remain out of scope

The second checker should therefore behave as follows on those samples:
- hard-fail only when a clearly migrated slice is missing `phase_id` or `rollback_strategy`
- ignore legacy sections that never claimed migrated structure
- avoid treating every `####` heading as automatically migrated

A practical deterministic boundary on the current samples is:
- headings like `#### Task A1`, `#### Task A2`, ... remain legacy and out of scope
- headings like `#### Slice A1`, `#### Slice B1`, `#### Slice C3`, ... are candidates for in-scope migrated slices
- the checker should only enter hard-fail mode once a slice heading is paired with migrated structural fields already present in that slice block

### 12.2.8 Phase 6 completion and expansion gate
Phase 6 should be considered sufficiently complete when all of the following are true:
- the first checker is implemented
- the first checker has at least minimal smoke coverage
- the second checker is implemented
- the second checker has at least minimal smoke coverage
- the current checker suite has one unified validation entrypoint
- that entrypoint is adopted by at least one closeout-oriented workflow and one acceptance-oriented workflow
- daily operational guidance says when to run the suite vs a single checker

Once those conditions are true, the default should be:
- stop adding new hard-fail rules immediately by reflex
- evaluate whether the next rule belongs in a later phase or a new implementation wave
- prefer tightening adoption, recovery, and workflow clarity before adding a third checker

A third checker should generally wait until at least one of these is true:
- the current two checkers produce repeated low-cost wins and no confusing false-positive pattern
- a repeated failure mode appears that is not already covered by the first two checkers
- there is a clear workflow gap that cannot be solved by better entrypoints or better recovery messaging

Signs that Phase 6 should pause before expanding further:
- operators still need to memorize too many entrypoints
- workflow adoption is partial or inconsistent
- current checker failures are still confusing to recover from
- the next candidate rule depends on fuzzy judgment instead of deterministic structure

### 12.2.9 Phase 6 closeout conclusion
Given the current workspace state, Phase 6 should now be treated as sufficiently landed.

Why:
- two deterministic hard-fail checkers now exist
- both checkers have minimal smoke coverage
- one unified validation entrypoint exists
- that entrypoint is already adopted in closeout and acceptance-oriented workflows
- daily operational guidance now explains which entrypoint to use

Recommended next default:
- do not add a third hard-fail checker as the automatic next move
- move the next implementation wave toward advisory checks or workflow-level improvements first
- only return to a new hard-fail checker when a repeated deterministic gap remains after the current suite has had time in use

Good next-wave candidates after Phase 6:
- advisory detection for oversized migration slices
- workflow-level reporting that summarizes which checker failed and what recovery path applies
- better closeout/acceptance UX around expected strategy gates such as `focus-first`

Recommended next-wave order:
1. advisory detection for oversized migration slices
2. workflow-level failure summarization and recovery hints
3. better strategy-gate UX around expected non-error failures such as `focus-first`

### 12.2.11 Exact contract for workflow-level failure summary
The next workflow-level improvement should summarize checker outcomes in operator-facing language without replacing the underlying command outputs.

#### Scope
This summary layer should sit above the current unified runner and describe:
- which hard-fail command failed, if any
- which advisory commands emitted warnings
- what the operator should inspect next

It should not become a second hidden checker layer.
The raw command outputs must remain visible or directly reachable.

#### Minimum output contract
The summary should:
- state whether the hard-fail suite passed or failed
- name the first failing hard-fail command when one exists
- list advisory commands that emitted warnings
- attach a short recovery hint that points to the relevant domain (`ACTIVE.md`, task doc structure, oversized slice review, etc.)

#### Non-goals
This workflow summary should not:
- suppress the underlying checker output
- invent recovery steps not supported by the checker contracts
- merge advisory warnings into hard-fail status
- become a fuzzy status essay

#### Recovery mapping
The first version should stay deterministic and shallow:
- `check_active_consistency.py` failure -> repair `ACTIVE.md` / repo drift first
- `check_task_slice_schema.py` failure -> repair migrated task slice structure first
- `check_oversized_migration_slices.py` advisory -> inspect whether the warned slice should split or tighten wording
- strategy-gate failures such as `focus-first` -> explain that this may be an expected policy gate rather than a broken checker

#### First output format
The first implementation should stay narrow.
It should append a small summary footer after raw command output, containing only:
- hard-fail status: `passed` or `failed`
- first failing hard-fail command, if any
- advisory commands that emitted warnings
- 1-line recovery hint per surfaced domain

It should not restructure the existing checker output body in this first wave.

Recommended slicing rule for that next wave:
- keep advisory checks non-blocking first
- prefer improving recovery/readability before adding new hard-fail policy
- require at least one real repeated operator pain point before promoting any advisory into a hard-fail rule

### 12.2.10 Exact contract for oversized migration slice advisory
The first advisory candidate after Phase 6 should warn when one migration slice has become too broad to map cleanly to visible progress.

#### Advisory scope
This advisory should look only at clearly migrated task docs and only at slice-shaped sections that already participate in the migrated structure.
It should not inspect legacy task sections that never claimed slice semantics.

#### Advisory signal
A slice should be considered a candidate for advisory warning only when there is a deterministic-enough structural trigger.

The first implementation should stay narrow and look for migrated slices where all of the following are true:
- the heading matches migrated slice semantics (`#### Slice ...`)
- the slice has a valid `phase_id`
- the slice does not already use a more specific sub-slice pattern such as `2A/2B` or similar split identifiers
- the slice `scope` list contains multiple entries
- the slice `done_definition` list contains multiple entries

This is intentionally narrower than the full human intuition of "too big".
It is acceptable for the first advisory to miss some oversized slices if that keeps false positives low.

#### Output mode
This rule should be advisory only.
It should:
- never fail the checker suite
- emit a warning-oriented summary instead of a hard error
- name the slice id / heading and the structural reason it looks oversized
- include a lightweight recovery hint for what the operator should inspect next
- suggest splitting the slice only when the warning is concrete enough to act on

Current reference trigger sample:
- the controlled fixtures in `tests/test_check_oversized_migration_slices.py` model the first broad `Slice P*` advisory trigger
- already split headings such as `Slice 2A` / `Slice 2B` should not be the primary target of the first advisory wave

#### Non-goals
This advisory should not:
- score prose quality in general
- force every large slice to split immediately
- reinterpret already completed historical slices with fuzzy hindsight
- upgrade to hard-fail just because a slice is subjectively "too big"

#### Recovery path
Recovery should stay lightweight:
1. inspect the named slice
2. decide whether visible progress is actually too heterogeneous for one slice id
3. if yes, split it into clearer sub-slices or tighten the slice wording
4. if no, leave it as-is and accept that the advisory is low-confidence noise to refine later

This closeout conclusion is a steering decision, not a ban.
If later evidence shows a clear deterministic gap with low false-positive cost, a third checker may still be justified in a later wave.

### 12.3 Anti-drift rules during migration
- do not create two live runtime sources of truth
- do not upgrade roadmap/tasks and ACTIVE in contradictory ways
- do not move rules into automation before the doc model stabilizes
- prefer partial structured migration over broad low-confidence rewrites

### 12.3.1 Adoption gates
A rule should generally enter checker/workflow only when:
- at least one real project has adopted the target structure successfully
- the rule can fail deterministically
- the false-positive cost is low enough
- the human recovery path is obvious

A rule should stay doc-only when:
- naming is still evolving
- the structure is only partially migrated
- the rule needs human judgment more than deterministic parsing

### 12.4 Completion threshold for migration work
A migration slice is considered solid when:
- the target file now matches the new model more closely than before
- no duplicate truth source is introduced
- ACTIVE remains recoverable
- consistency checks still pass

### 12.5 Post-alignment audit conclusion
Given the current workspace state, the biggest previously identified gaps against the final execution-system v1 have now been materially reduced:
- `closed_out` is no longer only a doc concept; it is encoded in closeout artifacts
- `validated` is no longer only implicit in validation lists; it is encoded in closeout artifact semantics
- acceptance no longer treats an intentionally non-auto-runnable focus as the same thing as a broken focus-first model
- ACTIVE has completed a second slimming pass on the execution-system roadmap activity card

Current remaining gaps are better understood as incremental improvements, not foundational model breaks.
Examples:
- more activity cards may still benefit from second-pass slimming
- slice state machine semantics are stronger in artifacts than in tasks docs themselves
- advisory/reporting quality can still improve without changing the core model

Default conclusion:
- do not keep expanding the execution-system line just because more polish is possible
- treat the core final-spec alignment work as substantially landed
- only open another execution-system slice when a concrete structural gap or repeated operator pain appears
- otherwise treat the execution-system line as in maintenance mode

### 12.6 Reopen conditions for the execution-system line
After the current audit conclusion, new execution-system slices should normally be opened only when at least one of the following is true:
- a structural rule in the final model is still missing from real workflow or artifact semantics
- operators repeatedly hit the same recovery ambiguity across sessions
- a current checker / advisory / acceptance path produces confusing or misleading results more than once
- a real project migration exposes a gap that the current six-layer model cannot represent cleanly

Things that do not justify reopening by themselves:
- "this output could be a little nicer"
- speculative future automation with no repeated pain signal
- broad cleanup energy without a concrete runtime-truth or recovery problem

### 12.6.1 Re-entry protocol
If the execution-system line needs to be reopened later:
1. record the concrete trigger (structural gap, repeated pain, misleading output, or migration mismatch)
2. state why the existing maintenance-mode posture is no longer sufficient
3. create a new slice only for that concrete gap
4. avoid reopening multiple speculative improvements at once

The re-entry move should be explicit and justified, not implicit drift back into open-ended system work.

### 12.7 Acceptance / summary / closeout integration plan
When this line is explicitly reopened for operator workflow quality, the preferred first integration wave is:
1. define a shared result model for hard-fail, advisory, policy-gate, and closeout-ready semantics
2. upgrade the unified runner footer from pure text assembly to a structured summary source
3. let acceptance consume the same result semantics instead of independently re-deriving them
4. add an explicit closeout-ready gate on top of the existing closeout prepare flow
5. add chain-level smoke coverage for pass/advisory, hard-fail, and policy-gate paths

Constraints for this wave:
- keep raw command output visible
- do not silently promote advisory to hard-fail
- do not rewrite the six-layer model
- prefer thin orchestration over a new state platform

## 13. Versioning / migration guidance

This document is `v1` of the execution system spec.

Migration principle:
- prefer additive migration over big-bang replacement
- land docs/templates first
- migrate active projects gradually
- do not create duplicate runtime truth during migration

For current workspace policy, `ACTIVE.md` remains the runtime source of truth throughout migration.
