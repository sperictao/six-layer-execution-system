#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
ACTIVE = WORKSPACE / "ACTIVE.md"
CHECK_ACTIVE = WORKSPACE / "scripts" / "check_active_consistency.py"
CHECK_WAVE = WORKSPACE / "scripts" / "check_active_wave_state.py"


def run(script: Path, active_path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(script), str(active_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def expect(output: str, needle: str) -> None:
    if needle not in output:
        raise AssertionError(f"missing expected text: {needle}\n{output}")


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise AssertionError(f"missing expected fixture text: {old}")
    return text.replace(old, new, 1)


def main() -> int:
    original = ACTIVE.read_text(encoding="utf-8")
    synthetic = original
    synthetic = replace_once(
        synthetic,
        "- current_wave_id: `W1`\n",
        "- current_wave_id: `Wsynthetic`\n",
    )
    synthetic = replace_once(
        synthetic,
        "- ready_slices:\n  - `switch-focus-one-publish-advisory-convergence`\n",
        "- ready_slices:\n  - `PW-A.A2`\n",
    )
    synthetic = replace_once(
        synthetic,
        "- inflight_slices:\n  - `DX-E.E10`\n",
        "- inflight_slices:\n  - `PW-A.A1`\n",
    )
    synthetic = replace_once(
        synthetic,
        "- integration_step:\n  - 将 execution-system-decomposition-upgrade 当前轮的 closeout 状态保留下来，并把下一条实现主线正式交回 `one-publish-advisory-convergence`\n",
        "- integration_step:\n  - merge synthetic single-wave outputs into the next path-test decision\n",
    )
    synthetic = replace_once(
        synthetic,
        "- last_wave_result:\n  - `W10 multi-wave no-go closeout complete: later-multi-wave remains documented as a no-go discovery cut with a future reopen condition`\n",
        "- last_wave_result:\n  - `Wsynthetic-0 complete: fixture seeded for single-wave path validation`\n",
    )

    with tempfile.TemporaryDirectory(prefix="exec-system-parallel-wave-") as tmpdir:
        active_path = Path(tmpdir) / "ACTIVE.md"
        active_path.write_text(synthetic, encoding="utf-8")

        code, output = run(CHECK_WAVE, active_path)
        if code != 0:
            raise AssertionError(output)
        expect(output, "ACTIVE_WAVE_STATE_CHECK_OK")

        code, output = run(CHECK_ACTIVE, active_path)
        if code != 0:
            raise AssertionError(output)
        expect(output, "CONSISTENCY_CHECK_OK")
        expect(output, "- focus_activity_id: waiting-ledger-review")
        expect(output, "- focus_type: waiting")
        expect(output, "- focus_status: blocked")

    print("EXECUTION_SYSTEM_PARALLEL_WAVE_PATH_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
