#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from test_workspace_clone import cloned_workspace, workspace_env


def expect(output: str, needle: str) -> None:
    if needle not in output:
        raise AssertionError(f"missing expected text: {needle}\n{output}")


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise AssertionError(f"missing expected fixture text: {old}")
    return text.replace(old, new, 1)


def run_with_env(script: Path, active_path: Path, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(script), str(active_path)],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        active_path = workspace / "ACTIVE.md"
        active_text = active_path.read_text(encoding="utf-8")
        active_text = replace_once(
            active_text,
            "- current_focus_activity_id: `waiting-ledger-review`",
            "- current_focus_activity_id: `execution-system-decomposition-upgrade`",
        )
        active_text = replace_once(
            active_text,
            "- default_reply_activity_id: `waiting-ledger-review`",
            "- default_reply_activity_id: `execution-system-decomposition-upgrade`",
        )
        active_path.write_text(active_text, encoding="utf-8")

        card_path = workspace / "activities" / "execution-system-decomposition-upgrade" / "card.md"
        synthetic = card_path.read_text(encoding="utf-8")
        synthetic = replace_once(
            synthetic,
            "- current_wave_id: `W1`\n",
            "- current_wave_id: `Wsynthetic`\n",
        )
        synthetic = replace_once(
            synthetic,
            "- ready_slices:\n  - `switch-focus-waiting-ledger-review`\n",
            "- ready_slices:\n  - `PW-A.A2`\n",
        )
        synthetic = replace_once(
            synthetic,
            "- inflight_slices:\n  - `DX-E.E10`\n",
            "- inflight_slices:\n  - `PW-A.A1`\n",
        )
        synthetic = replace_once(
            synthetic,
            "- integration_step:\n  - 将 execution-system-decomposition-upgrade 当前轮的 closeout 状态保留下来，并把下一条默认 review focus 交回 `waiting-ledger-review`\n",
            "- integration_step:\n  - merge synthetic single-wave outputs into the next path-test decision\n",
        )
        synthetic = replace_once(
            synthetic,
            "- last_wave_result:\n  - `W10 multi-wave no-go closeout complete: later-multi-wave remains documented as a no-go discovery cut with a future reopen condition`\n",
            "- last_wave_result:\n  - `Wsynthetic-0 complete: fixture seeded for single-wave path validation`\n",
        )
        card_path.write_text(synthetic, encoding="utf-8")

        check_wave = workspace / "scripts" / "check_active_wave_state.py"
        check_active = workspace / "scripts" / "check_active_consistency.py"

        code, output = run_with_env(check_wave, active_path, env)
        if code != 0:
            raise AssertionError(output)
        expect(output, "ACTIVE_WAVE_STATE_CHECK_OK")

        code, output = run_with_env(check_active, active_path, env)
        if code != 0:
            raise AssertionError(output)
        expect(output, "CONSISTENCY_CHECK_OK")
        expect(output, "- focus_activity_id: execution-system-decomposition-upgrade")
        expect(output, "- focus_type: roadmap")
        expect(output, "- focus_status: ready")

    print("EXECUTION_SYSTEM_PARALLEL_WAVE_PATH_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
