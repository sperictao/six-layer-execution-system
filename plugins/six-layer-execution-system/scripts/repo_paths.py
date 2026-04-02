#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(
    os.environ.get("SIX_LAYER_REPO_ROOT", Path(__file__).resolve().parents[1])
).expanduser().resolve()
WORKSPACE = Path(
    os.environ.get("SIX_LAYER_WORKSPACE", REPO_ROOT)
).expanduser().resolve()
STATE_ROOT = Path(
    os.environ.get("SIX_LAYER_STATE_ROOT", REPO_ROOT / "local-state")
).expanduser().resolve()
CONFIG_PATH = Path(
    os.environ.get("SIX_LAYER_CONFIG_PATH", STATE_ROOT / "openclaw.json")
).expanduser().resolve()
PACKAGE_ROOT = Path(
    os.environ.get("OPENCLAW_PACKAGE_ROOT", "/opt/homebrew/lib/node_modules/openclaw")
).expanduser().resolve()
CLI_PATH = os.environ.get("OPENCLAW_CLI_PATH") or shutil.which("openclaw") or "openclaw"
