#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from execution_system_paths import WORKSPACE
from test_workspace_clone import cloned_workspace, workspace_env

sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "scripts"))

import scripts.accept_active_ledger_v2 as acceptance
import scripts.active_ledger as active_ledger
import scripts.check_closeout_ready as closeout_ready
import scripts.check_execution_system_maintenance_mode as maintenance_mode
import scripts.inspect_openclaw_execution_system as inspect_openclaw
import scripts.validate_focus_first as validate_focus_first


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_script(
    script: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env.update(env or {})
    return subprocess.run(
        ["python3", str(script), *args],
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def capture_main(fn) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = int(fn())
    return code, buffer.getvalue()


class FakeActivity:
    def __init__(self, activity_id: str, **fields):
        self.activity_id = activity_id
        self.heading = activity_id
        self._fields = fields

    def scalar(self, key: str, default: str | None = None):
        value = self._fields.get(key, default)
        return value if isinstance(value, str) else default

    def items(self, key: str):
        value = self._fields.get(key, [])
        return list(value) if isinstance(value, list) else []

    def as_dict(self) -> dict:
        return {
            "heading": self.heading,
            "fields": dict(self._fields),
            "list_fields": {},
        }


class FakeLedger:
    def __init__(
        self,
        focus: FakeActivity | None,
        *,
        execution_activity: FakeActivity | None = None,
        runnable: list[FakeActivity] | None = None,
    ):
        self._focus = focus
        self._execution_activity = execution_activity
        self._runnable = list(runnable or [])

    def get_current_focus_activity(self):
        return self._focus

    def get_activity(self, activity_id: str):
        if activity_id == "execution-system-spec-v1":
            return self._execution_activity
        if self._focus and self._focus.activity_id == activity_id:
            return self._focus
        return None

    def list_runnable_activities(self):
        return list(self._runnable)


class RaisingLoader:
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raise RuntimeError("bad import")


def main() -> int:
    expect(
        active_ledger._parse_backtick_value("- version: `2`", "version") == "2",
        "backtick parser should extract values",
    )
    expect(
        active_ledger._parse_backtick_value("- version: 2", "version") is None,
        "backtick parser should reject non-backtick values",
    )
    expect(
        active_ledger._parse_simple_value("- owner: Spero", "owner") == "Spero",
        "simple parser should extract values",
    )
    expect(
        active_ledger._extract_section(["## A", "x", "## B"], "Missing") == [],
        "extract_section should return empty list for missing title",
    )

    sample_ledger = """# ACTIVE

## Ledger meta
- version: `2`
- current_focus_activity_id: `beta`

## Activity index
- `beta`
- `alpha`

## Activities
### Activity: alpha
- activity_id: `alpha`
- title: `Alpha`
- type: `roadmap`
- status: `ready`
- autopilot: `true`
- path: `<plugin-root>/docs`
- repo: `alpha-repo`
- current_slice_id: `AL-1`
- next_slice_id: `AL-2`
- last_commit: `aaa111`
- blocked_by:
  - none

### Activity: beta
- activity_id: `beta`
- title: `Beta`
- type: `roadmap`
- status: `in_progress`
- autopilot: `true`
- current_slice_id: `BE-1`
- next_slice_id: `BE-2`
- last_commit: `bbb222`
- blocked_by:
  - alpha

### Activity: gamma
- activity_id: `gamma`
- title: `Gamma`
- type: `waiting`
- status: `ready`
- autopilot: `true`

### Activity: delta
- activity_id: `delta`
- title: `Delta`
- type: `roadmap`
- status: `ready`
- autopilot: `true`
"""
    with tempfile.TemporaryDirectory(prefix="six-layer-ledger-") as tmpdir:
        ledger_path = Path(tmpdir) / "ACTIVE.md"
        ledger_path.write_text(sample_ledger, encoding="utf-8")
        ledger = active_ledger.parse_ledger(ledger_path)
        focus = ledger.get_current_focus_activity()
        expect(focus is not None, "synthetic ledger should have focus")
        expect(focus.activity_id == "beta", ledger.as_dict().__repr__())
        expect(ledger.get_activity("missing") is None, "missing activity should return None")
        ordered_ids = [activity.activity_id for activity in ledger.list_activities()]
        expect(ordered_ids == ["beta", "alpha", "gamma", "delta"], str(ordered_ids))
        runnable_ids = [activity.activity_id for activity in ledger.list_runnable_activities()]
        expect(runnable_ids == ["alpha", "delta"], str(runnable_ids))
        expect(focus.scalar("title") == "Beta", focus.as_dict().__repr__())
        expect(focus.scalar("missing", "fallback") == "fallback", focus.as_dict().__repr__())
        expect(ledger.get_activity("alpha").repo_path == "<plugin-root>/docs", ledger.as_dict().__repr__())
        expect(ledger.get_activity("alpha").repo_name == "alpha-repo", ledger.as_dict().__repr__())
        expect(ledger.get_activity("alpha").current_slice_id == "AL-1", ledger.as_dict().__repr__())
        expect(ledger.get_activity("alpha").next_slice_id == "AL-2", ledger.as_dict().__repr__())
        expect(ledger.get_activity("alpha").last_commit == "aaa111", ledger.as_dict().__repr__())
        expect(ledger.get_activity("alpha").items("blocked_by") == ["none"], ledger.as_dict().__repr__())
        dumped = active_ledger.dump_current_focus(ledger_path)
        expect(dumped["focus_activity_id"] == "beta", str(dumped))
        expect(dumped["focus"]["fields"]["title"] == "Beta", str(dumped))

    with tempfile.TemporaryDirectory(prefix="six-layer-ledger-empty-") as tmpdir:
        ledger_path = Path(tmpdir) / "ACTIVE.md"
        ledger_path.write_text("# ACTIVE\n\n## Ledger meta\n- version: `2`\n", encoding="utf-8")
        dumped = active_ledger.dump_current_focus(ledger_path)
        expect(dumped["focus"] is None, str(dumped))
        expect(active_ledger.get_current_focus_activity(ledger_path) is None, str(dumped))

    proc = subprocess.run(
        ["python3", str(WORKSPACE / "scripts" / "active_ledger.py")],
        text=True,
        capture_output=True,
        check=False,
    )
    expect(proc.returncode == 0, proc.stdout + proc.stderr)
    active_snapshot = json.loads(proc.stdout)
    expect(active_snapshot["meta"]["current_focus_activity_id"] == "waiting-ledger-review", proc.stdout + proc.stderr)

    with mock.patch.object(inspect_openclaw.subprocess, "check_output", return_value="OpenClaw 1.0\n"):
        expect(inspect_openclaw.run_text(["openclaw", "--version"]) == "OpenClaw 1.0", "run_text should trim output")
    with mock.patch.object(inspect_openclaw.subprocess, "check_output", side_effect=RuntimeError("boom")):
        expect(inspect_openclaw.run_text(["openclaw", "--version"]) is None, "run_text should swallow exceptions")

    redacted = inspect_openclaw.redact(
        {
            "token": "secret",
            "apiKey": "secret",
            "ApiKey": "secret",
            "nested": [{"clientSecret": "secret"}, {"monkey": "banana"}, {"otherKey": "secret"}],
        }
    )
    expect(redacted["token"] == "<redacted>", str(redacted))
    expect(redacted["apiKey"] == "<redacted>", str(redacted))
    expect(redacted["ApiKey"] == "<redacted>", str(redacted))
    expect(redacted["nested"][0]["clientSecret"] == "<redacted>", str(redacted))
    expect(redacted["nested"][1]["monkey"] == "banana", str(redacted))
    expect(redacted["nested"][2]["otherKey"] == "<redacted>", str(redacted))

    original_config_path = inspect_openclaw.CONFIG_PATH
    original_workspace = inspect_openclaw.WORKSPACE
    try:
        with tempfile.TemporaryDirectory(prefix="six-layer-config-") as tmpdir:
            tmp_root = Path(tmpdir)
            inspect_openclaw.CONFIG_PATH = tmp_root / "openclaw.json"
            expect(inspect_openclaw.load_config_summary() == {"exists": False}, "missing config should return exists false")
            inspect_openclaw.CONFIG_PATH.write_text(
                json.dumps({"agents": {"a": 1}, "ignored": True, "providers": {"token": "x"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            config_summary = inspect_openclaw.load_config_summary()
            expect(config_summary["exists"] is True, str(config_summary))
            expect("ignored" not in config_summary["data"], str(config_summary))
            expect(config_summary["data"]["providers"]["token"] == "<redacted>", str(config_summary))

        with tempfile.TemporaryDirectory(prefix="six-layer-missing-workspace-") as tmpdir:
            inspect_openclaw.WORKSPACE = Path(tmpdir)
            expect(inspect_openclaw.load_ledger_summary() == {"exists": False}, "missing workspace should report exists false")

        with mock.patch.object(inspect_openclaw.importlib.util, "spec_from_file_location", return_value=SimpleNamespace(loader=None)):
            inspect_openclaw.WORKSPACE = original_workspace
            summary = inspect_openclaw.load_ledger_summary()
            expect(summary == {"exists": False, "error": "cannot import active_ledger.py"}, str(summary))

        with mock.patch.object(
            inspect_openclaw.importlib.util,
            "spec_from_file_location",
            return_value=SimpleNamespace(loader=RaisingLoader(), name="active_ledger"),
        ):
            with mock.patch.object(inspect_openclaw.importlib.util, "module_from_spec", return_value=SimpleNamespace()):
                inspect_openclaw.WORKSPACE = original_workspace
                summary = inspect_openclaw.load_ledger_summary()
                expect(summary["exists"] is False and "ledger import failed" in summary["error"], str(summary))

        with cloned_workspace() as workspace:
            inspect_openclaw.WORKSPACE = workspace
            ledger_summary = inspect_openclaw.load_ledger_summary()
            expect(ledger_summary["exists"] is True, str(ledger_summary))
            expect(ledger_summary["current_focus_activity_id"] == "waiting-ledger-review", str(ledger_summary))
    finally:
        inspect_openclaw.CONFIG_PATH = original_config_path
        inspect_openclaw.WORKSPACE = original_workspace

    markdown_missing = inspect_openclaw.to_markdown(
        {
            "repo": {"root": "/repo"},
            "cli": {"path": "openclaw", "version": None},
            "package": {"root": "/pkg"},
            "state_root": "/state",
            "workspace": {"root": "/workspace", "docs": []},
            "ledger": {"exists": False},
            "config": {"exists": False},
        }
    )
    expect("- ledger: missing" in markdown_missing, markdown_missing)
    expect("- config: missing" in markdown_missing, markdown_missing)

    markdown_present = inspect_openclaw.to_markdown(
        {
            "repo": {"root": "/repo"},
            "cli": {"path": "openclaw", "version": "1.0"},
            "package": {"root": "/pkg"},
            "state_root": "/state",
            "workspace": {"root": "/workspace", "docs": ["docs/a.md"]},
            "ledger": {
                "exists": True,
                "current_focus_activity_id": "focus",
                "default_reply_activity_id": "focus",
                "activities": [
                    {
                        "activity_id": "focus",
                        "type": "roadmap",
                        "status": "ready",
                        "current_slice_id": "A1",
                        "next_slice_id": "A2",
                    }
                ],
            },
            "config": {"exists": True, "data": {"providers": {"token": "<redacted>"}}},
        }
    )
    expect("- execution_doc: `docs/a.md`" in markdown_present, markdown_present)
    expect("```json" in markdown_present, markdown_present)

    original_build_snapshot = inspect_openclaw.build_snapshot
    old_argv = sys.argv[:]
    try:
        inspect_openclaw.build_snapshot = lambda: {
            "repo": {"root": "/repo"},
            "cli": {"path": "openclaw", "version": "1.0"},
            "package": {"root": "/pkg"},
            "state_root": "/state",
            "workspace": {"root": "/workspace", "docs": []},
            "ledger": {"exists": False},
            "config": {"exists": False},
        }
        buffer = io.StringIO()
        sys.argv = ["inspect_openclaw_execution_system.py", "--format", "json"]
        with contextlib.redirect_stdout(buffer):
            code = int(inspect_openclaw.main())
        expect(code == 0, buffer.getvalue())
        expect(json.loads(buffer.getvalue())["repo"]["root"] == "/repo", buffer.getvalue())

        buffer = io.StringIO()
        sys.argv = ["inspect_openclaw_execution_system.py"]
        with contextlib.redirect_stdout(buffer):
            code = int(inspect_openclaw.main())
        expect(code == 0, buffer.getvalue())
        expect("# Six-Layer Execution System Snapshot" in buffer.getvalue(), buffer.getvalue())
    finally:
        inspect_openclaw.build_snapshot = original_build_snapshot
        sys.argv = old_argv

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        active_path = workspace / "ACTIVE.md"
        set_focus = workspace / "scripts" / "set_focus_activity.py"

        proc = run_script(set_focus, env=env)
        expect(proc.returncode == 2, proc.stdout + proc.stderr)
        expect("usage: set_focus_activity.py <activity_id>" in proc.stderr, proc.stdout + proc.stderr)

        proc = run_script(set_focus, "missing-activity", env=env)
        expect(proc.returncode == 1, proc.stdout + proc.stderr)
        expect("UNKNOWN_ACTIVITY:missing-activity" in proc.stderr, proc.stdout + proc.stderr)

        original_text = active_path.read_text(encoding="utf-8")
        active_path.write_text(original_text.replace("- current_focus_activity_id: `waiting-ledger-review`\n", ""), encoding="utf-8")
        proc = run_script(set_focus, "execution-system-decomposition-upgrade", env=env)
        expect(proc.returncode == 1, proc.stdout + proc.stderr)
        expect("MISSING_CURRENT_FOCUS" in proc.stderr, proc.stdout + proc.stderr)

        active_path.write_text(original_text.replace("- default_reply_activity_id: `waiting-ledger-review`\n", ""), encoding="utf-8")
        proc = run_script(set_focus, "execution-system-decomposition-upgrade", env=env)
        expect(proc.returncode == 1, proc.stdout + proc.stderr)
        expect("MISSING_DEFAULT_REPLY_ACTIVITY" in proc.stderr, proc.stdout + proc.stderr)

        active_path.write_text(original_text, encoding="utf-8")
        proc = run_script(set_focus, "execution-system-decomposition-upgrade", env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "execution-system-decomposition-upgrade", proc.stdout + proc.stderr)
        updated_text = active_path.read_text(encoding="utf-8")
        expect("- current_focus_activity_id: `execution-system-decomposition-upgrade`" in updated_text, updated_text)
        expect("- default_reply_activity_id: `execution-system-decomposition-upgrade`" in updated_text, updated_text)

    original_parse_focus = validate_focus_first.parse_ledger
    try:
        validate_focus_first.parse_ledger = lambda: FakeLedger(None)
        code, output = capture_main(validate_focus_first.main)
        expect(code == 1, output)
        expect("FOCUS_VALIDATION_FAILED:no_focus" in output, output)

        focus = FakeActivity("focus", autopilot="true", type="roadmap")
        other = FakeActivity("other", autopilot="true", type="roadmap")
        validate_focus_first.parse_ledger = lambda: FakeLedger(focus, runnable=[focus, other])
        code, output = capture_main(validate_focus_first.main)
        expect(code == 0, output)
        expect("FOCUS_VALIDATION_OK" in output, output)
        expect("- non_focus_runnable_count: 1" in output, output)
    finally:
        validate_focus_first.parse_ledger = original_parse_focus

    original_collect_closeout = closeout_ready.collect_summary
    original_parse_closeout = closeout_ready.parse_ledger
    try:
        closeout_ready.collect_summary = lambda print_output=False: (
            0,
            SimpleNamespace(hard_fail_status="passed", first_failing_command=None, advisory_commands=["a"]),
        )
        closeout_ready.parse_ledger = lambda path: FakeLedger(None)
        code, output = capture_main(closeout_ready.main)
        expect(code == 1, output)
        expect("- reason: no focus activity" in output, output)

        closeout_ready.parse_ledger = lambda path: FakeLedger(FakeActivity("focus", type="roadmap", next_slice_id="B2", last_commit="abc", last_validation=["ok"]))
        code, output = capture_main(closeout_ready.main)
        expect(code == 1, output)
        expect("- reason: missing current_slice_id" in output, output)

        closeout_ready.parse_ledger = lambda path: FakeLedger(FakeActivity("focus", type="roadmap", current_slice_id="B1", last_commit="abc", last_validation=["ok"]))
        code, output = capture_main(closeout_ready.main)
        expect(code == 1, output)
        expect("- reason: missing next_slice_id" in output, output)

        closeout_ready.parse_ledger = lambda path: FakeLedger(FakeActivity("focus", type="roadmap", current_slice_id="B1", next_slice_id="B2", last_validation=["ok"]))
        code, output = capture_main(closeout_ready.main)
        expect(code == 1, output)
        expect("- reason: missing last_commit" in output, output)

        closeout_ready.parse_ledger = lambda path: FakeLedger(FakeActivity("focus", type="roadmap", current_slice_id="B1", next_slice_id="B2", last_commit="abc"))
        code, output = capture_main(closeout_ready.main)
        expect(code == 1, output)
        expect("- reason: missing last_validation entries" in output, output)
    finally:
        closeout_ready.collect_summary = original_collect_closeout
        closeout_ready.parse_ledger = original_parse_closeout

    original_parse_maintenance = maintenance_mode.parse_ledger
    original_subprocess_run = maintenance_mode.subprocess.run
    try:
        maintenance_mode.parse_ledger = lambda: FakeLedger(None, execution_activity=None)
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("- reason: missing execution-system-spec-v1 activity" in output, output)

        maintenance_mode.parse_ledger = lambda: FakeLedger(
            FakeActivity("focus", type="roadmap"),
            execution_activity=FakeActivity("execution-system-spec-v1", status="ready", autopilot="false"),
        )
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("execution-system status is not parked" in output, output)

        maintenance_mode.parse_ledger = lambda: FakeLedger(
            FakeActivity("focus", type="roadmap"),
            execution_activity=FakeActivity("execution-system-spec-v1", status="parked", autopilot="true"),
        )
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("execution-system autopilot is not false" in output, output)

        maintenance_mode.parse_ledger = lambda: FakeLedger(
            None,
            execution_activity=FakeActivity("execution-system-spec-v1", status="parked", autopilot="false"),
        )
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("- reason: no focus activity" in output, output)

        maintenance_mode.parse_ledger = lambda: FakeLedger(
            FakeActivity("execution-system-spec-v1", type="roadmap"),
            execution_activity=FakeActivity("execution-system-spec-v1", status="parked", autopilot="false"),
        )
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("execution-system should not remain the current focus" in output, output)

        maintenance_mode.parse_ledger = lambda: FakeLedger(
            FakeActivity("outside", type="roadmap"),
            execution_activity=FakeActivity("execution-system-spec-v1", status="parked", autopilot="false"),
            runnable=[],
        )
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("approved non-runnable focus" in output, output)

        maintenance_mode.parse_ledger = lambda: FakeLedger(
            FakeActivity("execution-system-decomposition-upgrade", type="roadmap"),
            execution_activity=FakeActivity("execution-system-spec-v1", status="parked", autopilot="false"),
            runnable=[],
        )
        maintenance_mode.subprocess.run = lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="bad\n", stderr="")
        code, output = capture_main(maintenance_mode.main)
        expect(code == 1, output)
        expect("acceptance is not green under maintenance mode" in output, output)
    finally:
        maintenance_mode.parse_ledger = original_parse_maintenance
        maintenance_mode.subprocess.run = original_subprocess_run

    original_collect_acceptance = acceptance.collect_summary
    original_check_output = acceptance.subprocess.check_output
    original_compile = acceptance.py_compile.compile
    original_run_check = acceptance.run_check
    try:
        acceptance.collect_summary = lambda print_output=False: (
            0,
            SimpleNamespace(hard_fail_status="passed", first_failing_command=None, advisory_commands=["python3 check_oversized_migration_slices.py"]),
        )
        result, output = acceptance.run_check("execution-system-suite", ["python3", "dummy"])
        expect(result == "ok", output)
        expect("advisory_hits=1" in output, output)

        acceptance.collect_summary = lambda print_output=False: (
            1,
            SimpleNamespace(hard_fail_status="failed", first_failing_command="python3 failing", advisory_commands=[]),
        )
        result, output = acceptance.run_check("execution-system-suite", ["python3", "dummy"])
        expect(result == "fail", output)
        expect("first_failing_command=python3 failing" in output, output)

        acceptance.py_compile.compile = lambda *args, **kwargs: (_ for _ in ()).throw(
            py_compile.PyCompileError(SyntaxError, SyntaxError("boom"), "file.py")
        )
        result, output = acceptance.run_check("parser-pycompile", ["py_compile", "file.py"])
        expect(result == "fail", output)
        expect("SyntaxError: boom" in output, output)

        acceptance.py_compile.compile = lambda *args, **kwargs: None
        result, output = acceptance.run_check("parser-pycompile", ["py_compile", "file.py"])
        expect(result == "ok", output)
        expect("py_compile ok: file.py" in output, output)

        acceptance.subprocess.check_output = lambda *args, **kwargs: "ok\n"
        result, output = acceptance.run_check("focus-first", ["python3", "focus.py"])
        expect(result == "ok", output)
        expect(output == "ok", output)

        def raise_policy_gate(*args, **kwargs):
            raise subprocess.CalledProcessError(2, args[0], output="FOCUS_VALIDATION_POLICY_GATE\n- detail")

        acceptance.subprocess.check_output = raise_policy_gate
        result, output = acceptance.run_check("focus-first", ["python3", "focus.py"])
        expect(result == "policy_gate", output)
        expect("FOCUS_VALIDATION_POLICY_GATE" in output, output)

        def raise_fail(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], output="generic fail")

        acceptance.subprocess.check_output = raise_fail
        result, output = acceptance.run_check("focus-first", ["python3", "focus.py"])
        expect(result == "fail", output)
        expect(output == "generic fail", output)

        acceptance.run_check = lambda name, cmd: ("ok", "stubbed-ok")
        code, output = capture_main(acceptance.main)
        expect(code == 0, output)
        expect("ACTIVE_LEDGER_V2_ACCEPTANCE_OK" in output, output)
    finally:
        acceptance.collect_summary = original_collect_acceptance
        acceptance.subprocess.check_output = original_check_output
        acceptance.py_compile.compile = original_compile
        acceptance.run_check = original_run_check

    print("INTROSPECTION_AND_CONTROL_TOOLS_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
