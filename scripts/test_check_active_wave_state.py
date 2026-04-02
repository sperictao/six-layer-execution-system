#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_active_wave_state.py"
ACTIVE = WORKSPACE / "ACTIVE.md"


def run_checker(active_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CHECKER), str(active_path)],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_ok(name: str, proc: subprocess.CompletedProcess[str]) -> None:
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass, got {proc.stdout}{proc.stderr}")


def expect_fail(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail")
    output = proc.stdout + proc.stderr
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def replace_once(original: str, old: str, new: str) -> str:
    return original.replace(old, new, 1)


def main() -> int:
    original = ACTIVE.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="active-wave-state-") as tmpdir:
        tmp = Path(tmpdir)

        happy = tmp / "ACTIVE-happy.md"
        happy.write_text(original, encoding="utf-8")
        expect_ok("happy-path", run_checker(happy))

        valid_parallel = tmp / "ACTIVE-valid-parallel.md"
        valid_parallel.write_text(original, encoding="utf-8")
        expect_ok("valid-parallel-wave", run_checker(valid_parallel))

        missing_wave_id = tmp / "ACTIVE-missing-wave-id.md"
        missing_wave_id.write_text(
            replace_once(original, "- current_wave_id: `W1`\n", ""),
            encoding="utf-8",
        )
        expect_fail("missing-wave-id", run_checker(missing_wave_id), "missing `current_wave_id`")

        serial_conflict = tmp / "ACTIVE-serial-conflict.md"
        serial_conflict.write_text(
            replace_once(original, "- execution_mode: `parallel-wave`\n", "- execution_mode: `serial`\n"),
            encoding="utf-8",
        )
        expect_fail(
            "serial-wave-conflict",
            run_checker(serial_conflict),
            "wave-state fields should not be present when `execution_mode` is `serial`",
        )

    print("ACTIVE_WAVE_STATE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
