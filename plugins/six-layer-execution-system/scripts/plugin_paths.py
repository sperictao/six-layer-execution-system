#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ROOT_SCRIPTS = PLUGIN_ROOT / "scripts"
REPO_ROOT = Path(
    os.environ.get("SIX_LAYER_REPO_ROOT", PLUGIN_ROOT)
).expanduser().resolve()
WORKSPACE = Path(
    os.environ.get("SIX_LAYER_WORKSPACE", REPO_ROOT)
).expanduser().resolve()


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("SIX_LAYER_REPO_ROOT", str(REPO_ROOT))
    env.setdefault("SIX_LAYER_WORKSPACE", str(WORKSPACE))
    env.setdefault("SIX_LAYER_STATE_ROOT", str(REPO_ROOT / "local-state"))
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
