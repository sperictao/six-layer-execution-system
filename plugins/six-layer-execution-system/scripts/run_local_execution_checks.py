#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess

from execution_system_paths import WORKSPACE
from execution_system_suite import LOCAL_CHECK_MODES, workspace_python_command

COMMANDS = {
    mode: workspace_python_command(script_name)
    for mode, script_name in LOCAL_CHECK_MODES.items()
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canonical local Six-Layer execution-system checks.")
    parser.add_argument("mode", choices=sorted(COMMANDS))
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds. Default: 60.")
    args = parser.parse_args()

    cmd = COMMANDS[args.mode]
    print("==>", " ".join(cmd), flush=True)
    try:
        completed = subprocess.run(cmd, cwd=WORKSPACE, check=False, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"TIMED_OUT: {args.mode} exceeded {args.timeout}s")
        return 124
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
