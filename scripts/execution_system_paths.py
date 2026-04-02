#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

WORKSPACE = Path(
    os.environ.get("SIX_LAYER_WORKSPACE", Path(__file__).resolve().parents[1])
).expanduser().resolve()
SCRIPTS_DIR = WORKSPACE / "scripts"
ACTIVE_PATH = WORKSPACE / "ACTIVE.md"
DEFAULT_ONE_PUBLISH_TASK_DOC = WORKSPACE / "tasks" / "one-publish-refactor-tasks.md"
DEFAULT_EXECUTION_TESTING_TASK_DOC = (
    WORKSPACE / "tasks" / "execution-system-decomposition-upgrade-tasks.md"
)


def script_path(name: str) -> Path:
    return SCRIPTS_DIR / name


def command_str(name: str) -> str:
    return f"python3 {script_path(name)}"
