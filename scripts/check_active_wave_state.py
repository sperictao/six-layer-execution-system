#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from execution_system_paths import WORKSPACE
ACTIVE_PATH = WORKSPACE / "ACTIVE.md"
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402

WAVE_LIST_FIELDS = (
    "ready_slices",
    "inflight_slices",
    "blocked_slices",
    "integration_step",
    "last_wave_result",
)
WAVE_SCALAR_FIELDS = ("execution_mode", "current_wave_id")


def add_problem(problems: list[str], scope: str, message: str) -> None:
    problems.append(f"{scope}: {message}")


def has_any_wave_state(activity) -> bool:
    if any(activity.scalar(field) for field in WAVE_SCALAR_FIELDS):
        return True
    return any(activity.items(field) for field in WAVE_LIST_FIELDS)


def validate_task_doc(active_path: Path) -> list[str]:
    problems: list[str] = []
    ledger = parse_ledger(active_path)

    for activity in ledger.list_activities():
        scope = f"activity:{activity.activity_id or activity.heading}"
        activity_type = activity.scalar("type")
        wave_enabled = has_any_wave_state(activity)

        if not wave_enabled:
            continue

        if activity_type != "roadmap":
            add_problem(problems, scope, "wave-state fields are only allowed on roadmap activities")
            continue

        execution_mode = activity.scalar("execution_mode")
        current_wave_id = activity.scalar("current_wave_id")
        ready = activity.items("ready_slices")
        inflight = activity.items("inflight_slices")
        blocked = activity.items("blocked_slices")
        integration = activity.items("integration_step")

        if execution_mode not in {"serial", "parallel-wave"}:
            add_problem(problems, scope, "`execution_mode` must be `serial` or `parallel-wave`")
            continue

        if execution_mode == "serial":
            add_problem(problems, scope, "wave-state fields should not be present when `execution_mode` is `serial`")
            continue

        if not current_wave_id:
            add_problem(problems, scope, "missing `current_wave_id`")
        if not integration:
            add_problem(problems, scope, "missing list `integration_step`")
        if not (ready or inflight or blocked):
            add_problem(problems, scope, "parallel-wave activity must expose at least one of `ready_slices`, `inflight_slices`, or `blocked_slices`")

    return problems


def main() -> int:
    active_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ACTIVE_PATH
    problems = validate_task_doc(active_path)
    if problems:
        print("ACTIVE_WAVE_STATE_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("ACTIVE_WAVE_STATE_CHECK_OK")
    print(f"- active_doc: {active_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
