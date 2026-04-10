#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE))

from scripts.run_execution_system_checks import CHECKS, recovery_hint_for_command, summary_footer, build_summary  # noqa: E402


EXPECTED_HINTS = {
    "check_active_consistency.py": "repair ACTIVE.md or repo drift first",
    "check_demand_card_schema.py": "repair malformed demand intake fields before continuing",
    "check_generated_decomposition_consistency.py": "repair generated demand, roadmap, tasks, and ACTIVE drift before continuing",
    "check_task_slice_schema.py": "repair migrated task slice structure first",
    "check_task_dependency_graph.py": "repair slice dependency references or cycles before continuing",
    "check_parallel_safety.py": "repair unsafe parallel_safe declarations or missing shared_write_targets before continuing",
    "check_active_wave_state.py": "repair invalid ACTIVE wave-state fields or revert the pilot activity to lean non-wave execution before continuing",
    "check_execution_system_governance_consistency.py": "inspect spec/skill alignment and repair the drifted recovery rule",
    "check_execution_system_status_freshness.py": "remove baked-in full-suite health claims from durable docs and let live checks speak for current status",
}


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    seen = set()
    for command in CHECKS:
        script = Path(command[-1]).name
        if not script.startswith("check_"):
            continue
        seen.add(script)
        expected = EXPECTED_HINTS.get(script)
        if expected is None:
            raise AssertionError(f"missing expected hint mapping for {script}")

        actual = recovery_hint_for_command(command)
        if actual != expected:
            raise AssertionError(f"hint drift for {script}: {actual!r} != {expected!r}")

        summary = "\n".join(summary_footer(build_summary(" ".join(command), [])))
        expect(summary, f"- first_failing_command: {' '.join(command)}")
        expect(summary, f"- recovery_hint: {expected}")

    if seen != set(EXPECTED_HINTS):
        raise AssertionError(f"coverage drift: seen={seen!r}, expected={set(EXPECTED_HINTS)!r}")

    print("EXECUTION_SYSTEM_RUNNER_HINT_DRIFT_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
