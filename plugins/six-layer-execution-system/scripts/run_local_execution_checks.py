#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess

from plugin_paths import WORKSPACE

COMMANDS = {
    "active": ["python3", str(WORKSPACE / "scripts" / "check_active_consistency.py")],
    "checks": ["python3", str(WORKSPACE / "scripts" / "run_execution_system_checks.py")],
    "full-tests": ["python3", str(WORKSPACE / "scripts" / "run_execution_system_full_tests.py")],
    "closeout-ready": ["python3", str(WORKSPACE / "scripts" / "check_closeout_ready.py")],
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
