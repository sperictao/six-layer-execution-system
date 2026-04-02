# ACTIVE Ledger v2

## What it is

`ACTIVE.md` is the single runtime source of truth for multi-activity execution.

It uses a three-layer ledger model:

1. **Ledger meta**
   - global mode and focus selection
2. **Workspace rules**
   - execution / notification / closeout policy
3. **Activities**
   - each activity is an explicit work card

## Core rule

Only the **current focus activity** may enter autonomous execution.

Non-focus activities exist for:
- recovery
- tracking
- reminder context
- future switching

They must not be auto-advanced unless focus is explicitly changed.

## Activity types

### roadmap
Use for phased engineering / refactor / milestone work.

Expected fields include:
- `repo` / `path`
- `roadmap_doc`
- `tasks_doc`
- `current_slice_id`
- `next_slice_id`
- `last_commit`
- `next_step`
- `validation`
- `blocked_by`

### waiting
Use for blocked or waiting-on-human / waiting-on-external state.

Expected fields include:
- `waiting_on`
- `unblock_condition`
- `next_step`
- `validation`

Rules:
- must use `autopilot: false`
- must not be counted as runnable

### simple
Use for lightweight tasks that do not need roadmap/slice/commit semantics.

Expected fields include:
- `goal`
- `scope`
- `next_step`
- `validation`
- `done_definition`

Rules:
- no repo/slice/commit required
- still must be explicitly represented as an activity

## Focus-first workflow

### Read path
1. Read `Ledger meta`
2. Read `current_focus_activity_id`
3. Read that activity card first
4. Read other activities only if needed

### Execution path
- if focus activity is `autopilot=true`
- and status is runnable
- and blockers are clear
- then it may be auto-advanced

Otherwise:
- do not silently jump to another activity
- either stay idle or wait for an explicit focus switch

## Operational tools

### Validate ledger
```bash
python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/check_active_consistency.py
```

### Validate focus-first behavior
```bash
python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/validate_focus_first.py
```

Interpretation:
- `FOCUS_VALIDATION_OK` means focus is auto-runnable and also remains the only default execution path
- `FOCUS_VALIDATION_POLICY_GATE` means focus-first is still intact, but the current focus is intentionally not auto-runnable (for example `autopilot: false` on a roadmap activity, or a first-class `waiting` focus while the system is paused for human input)
- `FOCUS_VALIDATION_FAILED` means the focus-first model itself is broken or inconsistent

### Switch focus
```bash
python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/set_focus_activity.py <activity_id>
```

## Notification / closeout

For roadmap activities, closeout is activity-aware.

Deduplication key:
- `activity_id + completed_slice_id + commit`

Primary flow:
```bash
complete_slice.sh prepare
complete_slice.sh payload
# send message
complete_slice.sh ack <dedupe_key>
```

## Recovery checklist

When resuming:
1. read `ACTIVE.md`
2. identify focus activity
3. inspect related roadmap/tasks docs if focus is roadmap
4. run consistency checker if state seems suspicious
5. do not assume non-focus activities are executable

## Migration result

The old single-task interpretation is obsolete.

Do **not**:
- read the first `- path:` in the file and assume that is the active task
- infer current execution from arbitrary field order
- auto-run a non-focus activity
