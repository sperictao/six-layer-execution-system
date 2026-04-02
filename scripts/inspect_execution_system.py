#!/usr/bin/env python3
from __future__ import annotations

import sys

from plugin_paths import run_root_script


if __name__ == "__main__":
    raise SystemExit(run_root_script("inspect_openclaw_execution_system.py", sys.argv[1:]))
