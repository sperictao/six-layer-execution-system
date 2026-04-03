#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_RUNNER = REPO_ROOT / "plugins" / "six-layer-execution-system" / "scripts" / "run_execution_system_checks.py"

if str(PLUGIN_RUNNER.parent) not in sys.path:
    sys.path.insert(0, str(PLUGIN_RUNNER.parent))

spec = importlib.util.spec_from_file_location("six_layer_repo_runner", PLUGIN_RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Failed to load repo runner from {PLUGIN_RUNNER}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

CHECKS = module.CHECKS
ADVISORIES = module.ADVISORIES
REPO_SMOKE_TESTS = module.REPO_SMOKE_TESTS
ExecutionSystemSummary = module.ExecutionSystemSummary
WORKSPACE = module.WORKSPACE
Path = module.Path
subprocess = module.subprocess
_merged_pythonpath = module._merged_pythonpath
repo_test_env = module.repo_test_env
discover_repo_tests_root = module.discover_repo_tests_root
repo_test_commands = module.repo_test_commands
repo_smoke_status_for_reason = module.repo_smoke_status_for_reason
recovery_hint_for_command = module.recovery_hint_for_command
build_summary = module.build_summary
summary_footer = module.summary_footer
collect_summary = module.collect_summary
main = module.main


if __name__ == "__main__":
    raise SystemExit(main())
