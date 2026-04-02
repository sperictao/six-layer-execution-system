---
name: six-layer-execution-system
description: Inspect, explain, validate, repair, or port a focus-first six-layer execution-system repository whose plugin root stores runtime truth, including ACTIVE ledger rules, checker suites, closeout flows, and upstream OpenClaw runtime references.
---

# Six-Layer Execution System

Use this skill when the task is about a repository that follows the six-layer execution-system layout shipped with this plugin.

Treat the current repository as the subject:

- the plugin root is runtime truth.
- `references/` stores local docs and source maps.
- `scripts/` stores root entrypoints.
- `scripts/inspect_execution_system.py` and `scripts/run_execution_checks.py` are the plugin-safe wrapper commands.

## Quick Start

Follow this order unless the request is clearly narrower:

1. Run `python3 scripts/inspect_execution_system.py --format markdown`.
2. Read `references/local-install.md`.
3. Read `references/workspace-execution-system.md`.
4. If the task touches validation or closeout, read `references/checkers-and-protocols.md`.
5. If the task touches agent runtime, sandbox, tool policy, or upstream architecture, read `references/upstream-openclaw-runtime.md`.
6. Use `references/source-map.md` when you need exact file pointers before opening original files.

If you need to point these entrypoints at another extracted repo, override `SIX_LAYER_REPO_ROOT` and `SIX_LAYER_WORKSPACE` before running them.

## Operating Rules

- Trust `ACTIVE.md` at repo root for current runtime truth. Do not infer live execution state from memory logs or chat history.
- Keep the six-layer boundary intact: contract, roadmap, tasks, ACTIVE, decisions, memory.
- Treat focus-first execution as the default. Parallelize only inside the current focus activity and only when writes and runtime state do not conflict.
- Keep `ACTIVE.md` lean. Put rationale in `decisions/`; put history in `memory/`; put slice design in `tasks/`.
- Preserve explicit completion semantics. `validated` and `closed_out` must remain explicit artifact states, not inferred status.
- Redact secrets from local config before quoting or copying them.
- Prefer calling the existing wrapper commands and root checkers instead of recreating their logic in ad hoc code.
- When a request asks for a new protocol or schema field, inspect the current artifact, queue/state, payload, and checker surfaces first. Reuse an existing field only when it is semantically exact.

## Task Flows

### Explain or Audit the System

1. Run `python3 scripts/inspect_execution_system.py --format markdown`.
2. Read `references/workspace-execution-system.md` for local conventions.
3. Read `references/upstream-openclaw-runtime.md` for embedded agent, workspace, sandbox, and tool-policy mechanics.
4. Open original files only for the area you need to quote or modify.

### Recover Current Execution State

1. Read `ACTIVE.md`.
2. Resolve the current focus activity and its `source_doc`, `roadmap_doc`, and `tasks_doc`.
3. Verify repository and workspace facts before reporting status.
4. Read `memory/working-buffer.md` only as a recovery aid, never as runtime truth.

### Modify the Execution System

1. Decide which layer owns the requested change.
2. Before adding a new field or protocol surface, check whether an existing field already carries the same semantics.
3. If the user still requires a new explicit field name, add it without removing the old one, then update every downstream surface in one pass.
4. Edit only the owning layer plus any directly dependent validators or tests.
5. If the change affects recovery or closeout semantics, inspect:
   - `scripts/complete_slice.sh`
   - `scripts/create_slice_closeout.py`
   - `scripts/check_slice_closeout.py`
   - `scripts/check_closeout_ready.py`
6. If the change affects parallel-wave semantics, inspect:
   - `scripts/check_task_dependency_graph.py`
   - `scripts/check_parallel_safety.py`
   - `scripts/check_active_wave_state.py`
7. If the change affects runtime policy or prompts, inspect:
   - `AGENTS.md`
   - `HEARTBEAT.md`
   - the upstream runtime docs listed in `references/upstream-openclaw-runtime.md`

### Validate Changes

Use the plugin wrapper so the repository root and workspace env stay aligned:

```bash
python3 scripts/run_execution_checks.py active
python3 scripts/run_execution_checks.py checks
python3 scripts/run_execution_checks.py full-tests
```

Default to `checks`. Use `full-tests` for protocol, governance, or runner changes.

### Pick the Right Validation Shape

Use this decision rule when the change touches execution-system protocol surfaces:

1. If you changed one artifact field, one checker rule, or one payload field, run the nearest smoke test first.
2. If you changed a value that must survive across multiple surfaces, add or update a synthetic path test that walks the whole chain.
3. If you changed what the system claims is required for acceptance, update the acceptance checklist wording in the same slice.
4. If you changed runner composition or protocol behavior, rerun `full-tests`, not just `checks`.

Typical mapping:

- artifact field only -> `scripts/test_slice_closeout_state.py`
- checker gate only -> the nearest `scripts/test_check_*.py`
- artifact -> queue/state -> payload propagation -> add or update `scripts/test_execution_system_path_*`
- acceptance contract wording -> update `docs/execution-system-spec-v1-acceptance-checklist.md`

## Resources

- `scripts/inspect_openclaw_execution_system.py`: inspect the local installation and workspace snapshot.
- `scripts/run_local_execution_checks.py`: call the canonical local checker and full-test entrypoints with a bounded timeout.
- `scripts/inspect_execution_system.py`: plugin wrapper for the inspect entrypoint.
- `scripts/run_execution_checks.py`: plugin wrapper for the validation entrypoint.
