#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECK = WORKSPACE / "scripts" / "check_execution_system_governance_consistency.py"


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    proc = subprocess.run(["python3", str(CHECK)], text=True, capture_output=True, check=False)
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise AssertionError(output)

    expect(output, "EXECUTION_SYSTEM_GOVERNANCE_CONSISTENCY_OK")
    expect(output, "- maintenance_mode: documented")
    expect(output, "- reopen_conditions: documented")
    expect(output, "- reentry_protocol: documented")
    expect(output, "- resume_trigger_rule: documented")
    expect(output, "- prompt_authority: documented")
    expect(output, "- skill_recovery_alignment: documented")
    expect(output, "- skill_parallel_dispatch_alignment: documented")

    print("EXECUTION_SYSTEM_GOVERNANCE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
