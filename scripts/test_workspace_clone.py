#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from execution_system_paths import WORKSPACE


IGNORE_NAMES = {".git", ".clawhub", ".openclaw", "skills", "__pycache__", ".DS_Store"}


def _ignore(_src: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORE_NAMES}


@contextmanager
def cloned_workspace() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="six-layer-workspace-") as tmpdir:
        target = Path(tmpdir) / "workspace"
        shutil.copytree(WORKSPACE, target, ignore=_ignore)
        yield target


def workspace_env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["SIX_LAYER_REPO_ROOT"] = str(workspace)
    env["SIX_LAYER_WORKSPACE"] = str(workspace)
    return env


def init_git_repo(workspace: Path) -> str:
    subprocess.run(["git", "-C", str(workspace), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(workspace), "config", "user.name", "Codex Test"], check=True)
    subprocess.run(["git", "-C", str(workspace), "config", "user.email", "codex-test@example.com"], check=True)
    subprocess.run(["git", "-C", str(workspace), "add", "."], check=True)
    subprocess.run(["git", "-C", str(workspace), "commit", "-q", "-m", "test baseline"], check=True)
    return subprocess.check_output(
        ["git", "-C", str(workspace), "rev-parse", "--short", "HEAD"],
        text=True,
    ).strip()
