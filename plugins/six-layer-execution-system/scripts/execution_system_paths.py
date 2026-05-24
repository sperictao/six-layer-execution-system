#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

PLUGIN_ROOT_TOKEN = "<plugin-root>"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]

REPO_ROOT = Path(
    os.environ.get("SIX_LAYER_REPO_ROOT", PLUGIN_ROOT)
).expanduser().resolve()

WORKSPACE = Path(
    os.environ.get("SIX_LAYER_WORKSPACE", REPO_ROOT)
).expanduser().resolve()
STATE_ROOT = Path(
    os.environ.get("SIX_LAYER_STATE_ROOT", REPO_ROOT / "local-state")
).expanduser().resolve()
SCRIPTS_DIR = WORKSPACE / "scripts"
ACTIVE_PATH = WORKSPACE / "ACTIVE.md"
ACTIVITIES_DIR = WORKSPACE / "activities"
DEMANDS_DIR = WORKSPACE / "demands"  # legacy compatibility only
DEFAULT_MIGRATED_TASK_DOC = (
    WORKSPACE
    / "recycle"
    / "activities"
    / "execution-system-testing"
    / "3-tasks"
    / "execution-system-testing-tasks.md"
)
DEFAULT_PARALLEL_WAVE_TASK_DOC = (
    WORKSPACE / "tasks" / "execution-system-decomposition-upgrade-tasks.md"
)
DEFAULT_LEGACY_TASK_DOC = WORKSPACE / "tasks" / "active-ledger-v2-tasks.md"


def script_path(name: str) -> Path:
    return SCRIPTS_DIR / name


def command_str(name: str) -> str:
    return f"python3 {script_path(name)}"


def resolve_workspace_path(raw_path: str | Path | None) -> Path | None:
    if raw_path is None:
        return None

    text = str(raw_path).strip()
    if not text:
        return None

    if text in {".", PLUGIN_ROOT_TOKEN}:
        return WORKSPACE

    if text.startswith(f"{PLUGIN_ROOT_TOKEN}/"):
        relative = text[len(PLUGIN_ROOT_TOKEN) + 1 :]
        return (WORKSPACE / relative).resolve()

    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (WORKSPACE / candidate).resolve()
