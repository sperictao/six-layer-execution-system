#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from execution_system_paths import PLUGIN_ROOT, REPO_ROOT, STATE_ROOT, WORKSPACE

ROOT_SCRIPTS = PLUGIN_ROOT / "scripts"


def build_env() -> dict[str, str]:
    import os

    env = os.environ.copy()
    env.setdefault("SIX_LAYER_REPO_ROOT", str(REPO_ROOT))
    env.setdefault("SIX_LAYER_WORKSPACE", str(WORKSPACE))
    env.setdefault("SIX_LAYER_STATE_ROOT", str(STATE_ROOT))
    return env


def run_root_script(script_name: str, args: list[str]) -> int:
    script_path = ROOT_SCRIPTS / script_name
    completed = subprocess.run(
        ["python3", str(script_path), *args],
        cwd=PLUGIN_ROOT,
        env=build_env(),
        check=False,
    )
    return completed.returncode
