#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from execution_system_paths import PLUGIN_ROOT_TOKEN, WORKSPACE, command_str, resolve_workspace_path, script_path
from test_workspace_clone import cloned_workspace, workspace_env

import scripts.plugin_paths as plugin_paths
import scripts.run_execution_system_full_tests as full_tests
import scripts.run_local_execution_checks as run_local_checks


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_script(
    script: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["python3", str(script), *args],
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def run_python_expr(code: str, env: dict[str, str]) -> str:
    proc = subprocess.run(
        ["python3", "-c", code],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stdout + proc.stderr)
    return proc.stdout.strip()


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    expect(script_path("active_ledger.py") == WORKSPACE / "scripts" / "active_ledger.py", "script_path mismatch")
    expect(
        command_str("active_ledger.py") == f"python3 {WORKSPACE / 'scripts' / 'active_ledger.py'}",
        "command_str mismatch",
    )
    expect(resolve_workspace_path(None) is None, "resolve_workspace_path should keep None")
    expect(resolve_workspace_path("   ") is None, "resolve_workspace_path should drop blanks")
    expect(resolve_workspace_path(".") == WORKSPACE, "resolve_workspace_path should resolve . to workspace")
    expect(
        resolve_workspace_path(PLUGIN_ROOT_TOKEN) == WORKSPACE,
        "resolve_workspace_path should resolve <plugin-root> to workspace",
    )
    expect(
        resolve_workspace_path(f"{PLUGIN_ROOT_TOKEN}/docs") == (WORKSPACE / "docs").resolve(),
        "resolve_workspace_path should resolve <plugin-root>/relative",
    )
    expect(
        resolve_workspace_path("docs") == (WORKSPACE / "docs").resolve(),
        "resolve_workspace_path should resolve relative paths inside workspace",
    )
    expect(
        resolve_workspace_path(str((WORKSPACE / "docs").resolve())) == (WORKSPACE / "docs").resolve(),
        "resolve_workspace_path should keep absolute paths",
    )

    default_env = plugin_paths.build_env()
    expect(default_env["SIX_LAYER_REPO_ROOT"] == str(plugin_paths.REPO_ROOT), "build_env should expose repo root")
    expect(default_env["SIX_LAYER_WORKSPACE"] == str(plugin_paths.WORKSPACE), "build_env should expose workspace")
    expect(
        default_env["SIX_LAYER_STATE_ROOT"] == str(plugin_paths.REPO_ROOT / "local-state"),
        "build_env should expose state root",
    )

    with mock.patch.object(plugin_paths.subprocess, "run", return_value=SimpleNamespace(returncode=7)) as mocked_run:
        code = plugin_paths.run_root_script("inspect_openclaw_execution_system.py", ["--format", "json"])
    expect(code == 7, "run_root_script should return subprocess return code")
    called_args = mocked_run.call_args
    expect(called_args is not None, "subprocess.run should be called")
    expect(
        called_args.args[0] == ["python3", str(plugin_paths.ROOT_SCRIPTS / "inspect_openclaw_execution_system.py"), "--format", "json"],
        str(called_args.args[0]),
    )
    expect(called_args.kwargs["cwd"] == plugin_paths.PLUGIN_ROOT, str(called_args.kwargs))
    expect(called_args.kwargs["env"]["SIX_LAYER_REPO_ROOT"] == str(plugin_paths.REPO_ROOT), str(called_args.kwargs))

    with tempfile.TemporaryDirectory(prefix="six-layer-path-overrides-") as tmpdir:
        tmp_root = Path(tmpdir)
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": os.pathsep.join(
                    [
                        str(WORKSPACE / "scripts"),
                        env.get("PYTHONPATH", ""),
                    ]
                ),
                "SIX_LAYER_REPO_ROOT": str(tmp_root / "repo"),
                "SIX_LAYER_WORKSPACE": str(tmp_root / "workspace"),
                "SIX_LAYER_STATE_ROOT": str(tmp_root / "state"),
                "SIX_LAYER_CONFIG_PATH": str(tmp_root / "config" / "openclaw.json"),
                "OPENCLAW_PACKAGE_ROOT": str(tmp_root / "package"),
                "OPENCLAW_CLI_PATH": str(tmp_root / "bin" / "openclaw"),
            }
        )
        repo_paths_output = run_python_expr(
            "import json, repo_paths; print(json.dumps({'repo': str(repo_paths.REPO_ROOT), 'workspace': str(repo_paths.WORKSPACE), 'state': str(repo_paths.STATE_ROOT), 'config': str(repo_paths.CONFIG_PATH), 'package': str(repo_paths.PACKAGE_ROOT), 'cli': repo_paths.CLI_PATH}))",
            env,
        )
        repo_paths_payload = json.loads(repo_paths_output)
        expect(repo_paths_payload["repo"] == str((tmp_root / "repo").resolve()), repo_paths_output)
        expect(repo_paths_payload["workspace"] == str((tmp_root / "workspace").resolve()), repo_paths_output)
        expect(repo_paths_payload["state"] == str((tmp_root / "state").resolve()), repo_paths_output)
        expect(repo_paths_payload["config"] == str((tmp_root / "config" / "openclaw.json").resolve()), repo_paths_output)
        expect(repo_paths_payload["package"] == str((tmp_root / "package").resolve()), repo_paths_output)
        expect(repo_paths_payload["cli"] == str(tmp_root / "bin" / "openclaw"), repo_paths_output)

        plugin_paths_output = run_python_expr(
            "import json, plugin_paths; print(json.dumps({'repo': str(plugin_paths.REPO_ROOT), 'workspace': str(plugin_paths.WORKSPACE)}))",
            env,
        )
        plugin_paths_payload = json.loads(plugin_paths_output)
        expect(plugin_paths_payload["repo"] == str((tmp_root / "repo").resolve()), plugin_paths_output)
        expect(plugin_paths_payload["workspace"] == str((tmp_root / "workspace").resolve()), plugin_paths_output)

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        env["OPENCLAW_CLI_PATH"] = "python3"
        env["OPENCLAW_PACKAGE_ROOT"] = str(workspace)
        inspect_wrapper = workspace / "scripts" / "inspect_execution_system.py"
        checks_wrapper = workspace / "scripts" / "run_execution_checks.py"

        proc = run_script(inspect_wrapper, "--format", "json", env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        snapshot = json.loads(proc.stdout)
        expect(snapshot["workspace"]["root"] == str(workspace.resolve()), proc.stdout + proc.stderr)
        expect(snapshot["ledger"]["current_focus_activity_id"] == "waiting-ledger-review", proc.stdout + proc.stderr)

        proc = run_script(checks_wrapper, "checks", "--timeout", "60", env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect("EXECUTION_SYSTEM_CHECKS_OK" in proc.stdout, proc.stdout + proc.stderr)
        expect("- repo_smoke_tests: skipped" in proc.stdout, proc.stdout + proc.stderr)

    run_local_path = WORKSPACE / "scripts" / "run_local_execution_checks.py"
    run_local_module = load_module_from_path(run_local_path, "run_local_execution_checks_cov")
    with mock.patch.object(run_local_module.subprocess, "run", return_value=SimpleNamespace(returncode=9)) as mocked_run:
        buffer = io.StringIO()
        old_argv = sys.argv[:]
        try:
            sys.argv = ["run_local_execution_checks.py", "active", "--timeout", "12"]
            with contextlib.redirect_stdout(buffer):
                code = int(run_local_module.main())
        finally:
            sys.argv = old_argv
    expect(code == 9, buffer.getvalue())
    expect("==> python3" in buffer.getvalue(), buffer.getvalue())
    expect(mocked_run.call_args.kwargs["cwd"] == run_local_module.WORKSPACE, str(mocked_run.call_args.kwargs))
    expect(mocked_run.call_args.kwargs["timeout"] == 12, str(mocked_run.call_args.kwargs))

    timeout_module = load_module_from_path(run_local_path, "run_local_execution_checks_timeout_cov")
    with mock.patch.object(
        timeout_module.subprocess,
        "run",
        side_effect=subprocess.TimeoutExpired(cmd=["python3"], timeout=3),
    ):
        buffer = io.StringIO()
        old_argv = sys.argv[:]
        try:
            sys.argv = ["run_local_execution_checks.py", "closeout-ready", "--timeout", "3"]
            with contextlib.redirect_stdout(buffer):
                code = int(timeout_module.main())
        finally:
            sys.argv = old_argv
    expect(code == 124, buffer.getvalue())
    expect("TIMED_OUT: closeout-ready exceeded 3s" in buffer.getvalue(), buffer.getvalue())

    full_tests_path = WORKSPACE / "scripts" / "run_execution_system_full_tests.py"
    unavailable_module = load_module_from_path(full_tests_path, "run_execution_system_full_tests_unavailable_cov")
    with mock.patch.object(unavailable_module, "discover_repo_tests_root", return_value=(None, "tests missing")):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = int(unavailable_module.main())
    expect(code == 2, buffer.getvalue())
    expect("EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE" in buffer.getvalue(), buffer.getvalue())
    expect("- detail: tests missing" in buffer.getvalue(), buffer.getvalue())

    failing_module = load_module_from_path(full_tests_path, "run_execution_system_full_tests_failure_cov")

    def fake_subprocess_run(cmd, **_kwargs):
        if cmd[-1].endswith("test_execution_system_path_chain.py"):
            return SimpleNamespace(returncode=1, stdout="chain failed\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    tests_root = Path("/tmp/source-checkout/tests")
    with mock.patch.object(failing_module, "discover_repo_tests_root", return_value=(tests_root, None)):
        with mock.patch.object(failing_module, "repo_test_env", return_value={"PYTHONPATH": "x"}):
            with mock.patch.object(failing_module.subprocess, "run", side_effect=fake_subprocess_run):
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    code = int(failing_module.main())
    expect(code == 1, buffer.getvalue())
    expect("chain failed" in buffer.getvalue(), buffer.getvalue())
    expect("EXECUTION_SYSTEM_FULL_TESTS_FAILED" in buffer.getvalue(), buffer.getvalue())
    expect("- failed_test: system-path-happy" in buffer.getvalue(), buffer.getvalue())

    passing_module = load_module_from_path(full_tests_path, "run_execution_system_full_tests_ok_cov")
    with mock.patch.object(passing_module, "discover_repo_tests_root", return_value=(tests_root, None)):
        with mock.patch.object(passing_module, "repo_test_env", return_value={"PYTHONPATH": "x"}):
            with mock.patch.object(
                passing_module.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
            ):
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    code = int(passing_module.main())
    expect(code == 0, buffer.getvalue())
    expect("EXECUTION_SYSTEM_FULL_TESTS_OK" in buffer.getvalue(), buffer.getvalue())

    print("WRAPPER_AND_RUNNER_TOOLS_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
