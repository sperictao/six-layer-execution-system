#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import scripts.check_active_consistency as active_consistency
import scripts.check_closeout_ready as closeout_ready
import scripts.run_execution_system_checks as runner
import scripts.run_execution_system_full_tests as full_tests


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def capture_main(fn) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = int(fn())
    return code, buffer.getvalue()


class FakeActivity:
    def __init__(self, activity_id: str, heading: str | None = None, *, fields=None, list_fields=None):
        self.heading = heading or activity_id
        self.fields = dict(fields or {})
        self.fields.setdefault("activity_id", activity_id)
        self.list_fields = dict(list_fields or {})

    @property
    def activity_id(self):
        return self.fields.get("activity_id")

    @property
    def type(self):
        return self.fields.get("type")

    @property
    def status(self):
        return self.fields.get("status")

    @property
    def repo_path(self):
        return self.fields.get("path")

    @property
    def repo_name(self):
        return self.fields.get("repo")

    @property
    def current_slice_id(self):
        return self.fields.get("current_slice_id")

    @property
    def next_slice_id(self):
        return self.fields.get("next_slice_id")

    @property
    def last_commit(self):
        return self.fields.get("last_commit")

    def scalar(self, key: str, default=None):
        return self.fields.get(key, default)

    def items(self, key: str):
        return list(self.list_fields.get(key, []))


class FakeLedger:
    def __init__(self, meta=None, activities=None, activity_index=None):
        self.meta = dict(meta or {})
        self.activities = dict(activities or {})
        self.activity_index = list(activity_index or [])

    @property
    def current_focus_activity_id(self):
        return self.meta.get("current_focus_activity_id")

    def get_current_focus_activity(self):
        focus_id = self.current_focus_activity_id
        return self.activities.get(focus_id) if focus_id else None

    def list_activities(self):
        ordered = []
        seen = set()
        for activity_id in self.activity_index:
            if activity_id in self.activities:
                ordered.append(self.activities[activity_id])
                seen.add(activity_id)
        for activity_id, activity in self.activities.items():
            if activity_id not in seen:
                ordered.append(activity)
        return ordered

    def list_runnable_activities(self):
        return [
            activity
            for activity in self.list_activities()
            if activity.scalar("autopilot") == "true"
            and activity.scalar("status") in {"ready", "in_progress"}
            and activity.scalar("type") != "waiting"
            and (not activity.items("blocked_by") or activity.items("blocked_by") == ["none"])
        ]


def main() -> int:
    def fake_git_output(cmd, **kwargs):
        if "--is-inside-work-tree" in cmd:
            return "true\n"
        return "abc123\n"

    with mock.patch.object(active_consistency.subprocess, "check_output", side_effect=fake_git_output):
        expect(active_consistency.git_head("/tmp/repo") == "abc123", "git_head should trim output")
        expect(active_consistency.git_has_commit("/tmp/repo", "abc123"), "git_has_commit should return true on success")
        expect(active_consistency.git_repo_available("/tmp/repo"), "git_repo_available should return true for worktree")
    with mock.patch.object(active_consistency.subprocess, "check_output", side_effect=subprocess.CalledProcessError(1, ["git"])):
        expect(active_consistency.git_head("/tmp/repo") is None, "git_head should swallow git failures")
        expect(not active_consistency.git_has_commit("/tmp/repo", "abc123"), "git_has_commit should be false on failures")
        expect(not active_consistency.git_repo_available("/tmp/repo"), "git_repo_available should be false on failures")

    problems: list[str] = []
    active_consistency.add_problem(problems, "scope", "detail")
    expect(problems == ["scope: detail"], str(problems))

    activity = FakeActivity(
        "focus",
        fields={"title": "Focus"},
        list_fields={"validation": ["ok"]},
    )
    problems = []
    active_consistency.require_scalar(problems, "scope", activity, "title")
    active_consistency.require_scalar(problems, "scope", activity, "status")
    active_consistency.require_list(problems, "scope", activity, "validation")
    active_consistency.require_list(problems, "scope", activity, "next_step")
    scalar_list_activity = FakeActivity("scalar-list", fields={"next_step": "inline"})
    active_consistency.require_list(problems, "scope", scalar_list_activity, "next_step")
    expect(problems == ["scope: missing `status`", "scope: missing list `next_step`"], str(problems))

    with mock.patch.object(
        active_consistency.subprocess,
        "check_output",
        return_value=" M ACTIVE.md\nA  docs/spec.md\n\n",
    ):
        changed = active_consistency.git_changed_files("/tmp/repo")
    expect(changed == ["ACTIVE.md", "docs/spec.md"], str(changed))
    with mock.patch.object(active_consistency.subprocess, "check_output", side_effect=FileNotFoundError()):
        expect(active_consistency.git_changed_files("/tmp/repo") == [], "git_changed_files should swallow missing git")

    workspace_active = active_consistency.ACTIVE_PATH.relative_to(active_consistency.WORKSPACE).as_posix()
    expect(
        active_consistency.is_active_self_drift(str(active_consistency.WORKSPACE), [workspace_active]),
        "single ACTIVE.md drift should be treated as self drift",
    )
    expect(
        not active_consistency.is_active_self_drift(str(active_consistency.WORKSPACE), ["docs/spec.md"]),
        "non-ACTIVE drift should not be self drift",
    )
    expect(
        not active_consistency.is_active_self_drift("/tmp/other", [workspace_active]),
        "foreign repo path should not be self drift",
    )

    broken_ledger = FakeLedger(
        meta={"mode": "single", "selection_policy": "bad"},
        activities={},
        activity_index=["missing", "missing"],
    )
    problems = []
    active_consistency.validate_ledger_level(problems, broken_ledger)
    expect(any("missing `version`" in item for item in problems), str(problems))
    expect(any("mode must be `multi-activity`" in item for item in problems), str(problems))
    expect(any("Activity index contains duplicate" in item for item in problems), str(problems))
    expect(any("current focus activity" in item for item in problems), str(problems))

    problems = []
    active_consistency.validate_ledger_level(
        problems,
        FakeLedger(
            meta={
                "version": "2",
                "mode": "multi-activity",
                "current_focus_activity_id": "missing-focus",
                "default_reply_activity_id": "missing-reply",
                "selection_policy": "focus-first",
                "updated_at": "now",
            },
            activities={},
            activity_index=[],
        ),
    )
    expect(any("Activity index is empty" in item for item in problems), str(problems))
    expect(any("current focus activity `missing-focus` does not exist" in item for item in problems), str(problems))
    expect(any("default reply activity `missing-reply` does not exist" in item for item in problems), str(problems))

    roadmap = FakeActivity(
        "roadmap",
        fields={
            "title": "Roadmap",
            "type": "roadmap",
            "status": "weird",
            "priority": "P1",
            "autopilot": "maybe",
            "focus_rank": "0",
            "roadmap_doc": "",
            "tasks_doc": "",
            "next_step": "declared",
        },
        list_fields={"next_step": [], "validation": [], "blocked_by": []},
    )
    waiting = FakeActivity(
        "waiting",
        fields={
            "title": "Waiting",
            "type": "waiting",
            "status": "blocked",
            "priority": "P1",
            "autopilot": "true",
            "focus_rank": "1",
        },
    )
    simple = FakeActivity(
        "simple",
        fields={
            "title": "Simple",
            "type": "simple",
            "status": "ready",
            "priority": "P1",
            "autopilot": "false",
        },
    )
    odd = FakeActivity(
        "odd",
        fields={
            "title": "Odd",
            "type": "odd",
            "status": "ready",
            "priority": "P1",
            "autopilot": "false",
        },
    )
    missing_required = FakeActivity(
        "missing-required",
        heading="mismatch-heading",
        fields={
            "activity_id": "other-id",
            "type": "roadmap",
            "status": "ready",
            "priority": "P1",
            "autopilot": "false",
            "focus_rank": "0",
        },
    )
    problems = []
    active_consistency.validate_common_activity_fields(problems, missing_required)
    active_consistency.validate_common_activity_fields(problems, roadmap)
    active_consistency.validate_roadmap_activity(problems, roadmap)
    active_consistency.validate_waiting_activity(problems, waiting)
    active_consistency.validate_simple_activity(problems, simple)
    active_consistency.validate_activity_level(
        problems,
        FakeLedger(
            meta={"current_focus_activity_id": "roadmap"},
            activities={item.activity_id: item for item in [roadmap, waiting, simple, odd]},
            activity_index=["roadmap", "waiting", "simple", "odd"],
        ),
    )
    expect(any("status must be one of" in item for item in problems), str(problems))
    expect(any("autopilot must be `true` or `false`" in item for item in problems), str(problems))
    expect(any("missing `title`" in item for item in problems), str(problems))
    expect(any("must include `path` or `repo`" in item for item in problems), str(problems))
    expect(any("empty `roadmap_doc`" in item for item in problems), str(problems))
    expect(any("missing list `next_step`" in item for item in problems), str(problems))
    expect(any("waiting activity autopilot must be `false`" in item for item in problems), str(problems))
    expect(any("missing `waiting_on`" in item for item in problems), str(problems))
    expect(any("missing `goal`" in item for item in problems), str(problems))
    expect(any("missing list `next_step`" in item for item in problems), str(problems))
    expect(any("unsupported activity type `odd`" in item for item in problems), str(problems))
    expect(any("missing `focus_rank`" in item for item in problems), str(problems))

    focus = FakeActivity(
        "focus",
        fields={
            "title": "Focus",
            "type": "roadmap",
            "status": "",
            "priority": "P1",
            "autopilot": "false",
            "focus_rank": "0",
            "path": "relative/repo",
            "source_doc": "missing-source.md",
            "roadmap_doc": "missing-roadmap.md",
            "tasks_doc": "missing-tasks.md",
            "current_slice_id": "S1",
            "next_slice_id": "S1",
            "last_commit": "deadbeef",
        },
        list_fields={"next_step": [], "validation": [], "blocked_by": []},
    )
    focus_ledger = FakeLedger(
        meta={"current_focus_activity_id": "focus"},
        activities={"focus": focus},
        activity_index=["focus"],
    )
    active_consistency.validate_focus_level([], FakeLedger(meta={}, activities={}, activity_index=[]))
    problems = []
    with mock.patch.object(active_consistency, "resolve_workspace_path", return_value=None):
        active_consistency.validate_focus_level(problems, focus_ledger)
    expect(any("missing list `next_step`" in item for item in problems), str(problems))
    expect(any("points to missing file" in item for item in problems), str(problems))
    expect(any("missing `status`" in item for item in problems), str(problems))
    expect(any("current_slice_id and next_slice_id must differ" in item for item in problems), str(problems))
    expect(any("`path` is not resolvable" in item for item in problems), str(problems))

    focus_no_path = FakeActivity(
        "focus-no-path",
        fields={
            "title": "Focus No Path",
            "type": "roadmap",
            "status": "ready",
            "priority": "P1",
            "autopilot": "false",
            "focus_rank": "0",
            "source_doc": "missing-source.md",
            "roadmap_doc": "missing-roadmap.md",
            "tasks_doc": "missing-tasks.md",
            "current_slice_id": "S1",
            "next_slice_id": "S2",
            "last_commit": "deadbeef",
        },
        list_fields={"next_step": ["x"], "validation": ["y"], "blocked_by": ["none"]},
    )
    problems = []
    with mock.patch.object(active_consistency, "resolve_workspace_path", return_value=None):
        active_consistency.validate_focus_level(
            problems,
            FakeLedger(meta={"current_focus_activity_id": "focus-no-path"}, activities={"focus-no-path": focus_no_path}, activity_index=["focus-no-path"]),
        )
    expect(any("missing `path`" in item for item in problems), str(problems))

    temp_repo = Path(tempfile.mkdtemp(prefix="six-layer-focus-repo-"))
    problems = []
    with mock.patch.object(active_consistency, "resolve_workspace_path", return_value=temp_repo):
        with mock.patch.object(active_consistency, "git_repo_available", return_value=True):
            with mock.patch.object(active_consistency, "git_has_commit", return_value=False):
                with mock.patch.object(active_consistency, "git_head", side_effect=["head123", "head123"]):
                    with mock.patch.object(active_consistency, "git_changed_files", return_value=["docs/spec.md"]):
                        with mock.patch.object(active_consistency, "is_active_self_drift", return_value=False):
                            active_consistency.validate_focus_level(problems, focus_ledger)
    expect(any("last_commit `deadbeef` does not exist in repo" in item for item in problems), str(problems))
    expect(any("repo HEAD `head123` does not match last_commit `deadbeef`" in item for item in problems), str(problems))

    problems = []
    with mock.patch.object(active_consistency, "resolve_workspace_path", return_value=temp_repo):
        with mock.patch.object(active_consistency, "git_repo_available", return_value=True):
            with mock.patch.object(active_consistency, "git_has_commit", return_value=True):
                with mock.patch.object(active_consistency, "git_head", side_effect=["head456", "head456"]):
                    with mock.patch.object(active_consistency, "git_changed_files", return_value=[workspace_active]):
                        with mock.patch.object(active_consistency, "is_active_self_drift", return_value=True):
                            active_consistency.validate_focus_level(problems, focus_ledger)
    expect(sum("likely self-drift" in item for item in problems) == 2, str(problems))

    original_parse_consistency = active_consistency.parse_ledger
    try:
        active_consistency.parse_ledger = lambda path: focus_ledger
        code, output = capture_main(active_consistency.main)
        expect(code == 1, output)
        expect("CONSISTENCY_CHECK_FAILED" in output, output)

        happy_focus = FakeActivity(
            "happy",
            fields={
                "title": "Happy",
                "type": "roadmap",
                "status": "ready",
                "priority": "P1",
                "autopilot": "true",
                "focus_rank": "0",
                "path": str(active_consistency.WORKSPACE),
                "source_doc": "ACTIVE.md",
                "roadmap_doc": "roadmaps/execution-system-spec-v1-roadmap.md",
                "tasks_doc": "tasks/execution-system-spec-v1-tasks.md",
                "current_slice_id": "S1",
                "next_slice_id": "S2",
                "last_commit": "deadbeef",
            },
            list_fields={"next_step": ["x"], "validation": ["y"], "blocked_by": ["none"]},
        )
        happy_ledger = FakeLedger(
            meta={
                "version": "2",
                "mode": "multi-activity",
                "current_focus_activity_id": "happy",
                "default_reply_activity_id": "happy",
                "selection_policy": "focus-first",
                "updated_at": "now",
            },
            activities={"happy": happy_focus},
            activity_index=["happy"],
        )
        active_consistency.parse_ledger = lambda path: happy_ledger
        with mock.patch.object(active_consistency, "resolve_workspace_path", side_effect=lambda raw: active_consistency.WORKSPACE / raw if isinstance(raw, str) and not raw.startswith("/") else Path(raw)):
            with mock.patch.object(active_consistency, "git_repo_available", return_value=False):
                code, output = capture_main(active_consistency.main)
        expect(code == 0, output)
        expect("CONSISTENCY_CHECK_OK" in output, output)
        expect("- focus_status: ready" in output, output)
        expect("- last_commit: deadbeef" in output, output)
    finally:
        active_consistency.parse_ledger = original_parse_consistency

    os.environ["PYTHONPATH"] = os.pathsep.join(["dup", "dup"])
    merged = runner._merged_pythonpath([Path("dup"), Path("extra")])
    expect(str(runner.WORKSPACE) in merged, merged)
    expect(merged.split(os.pathsep).count("dup") == 1, merged)
    expect("extra" in merged, merged)
    env = runner.repo_test_env()
    expect(env["PYTHONPATH"] == runner._merged_pythonpath(), env["PYTHONPATH"])
    expect(runner.repo_smoke_status_for_reason("repo checkout detected at /tmp, but /tmp/tests is missing") == "unavailable", "repo smoke status should detect unavailable")
    expect(runner.repo_smoke_status_for_reason(None) == "skipped", "repo smoke status should default to skipped")
    expect("repair migrated task slice structure first" == runner.recovery_hint_for_command(["python3", "check_task_slice_schema.py"]), "slice schema hint mismatch")
    expect("repair slice dependency references or cycles before continuing" == runner.recovery_hint_for_command(["python3", "check_task_dependency_graph.py"]), "dependency hint mismatch")
    expect("repair unsafe parallel_safe declarations or missing shared_write_targets before continuing" == runner.recovery_hint_for_command(["python3", "check_parallel_safety.py"]), "parallel hint mismatch")
    expect("repair invalid ACTIVE wave-state fields or revert the pilot activity to lean non-wave execution before continuing" == runner.recovery_hint_for_command(["python3", "check_active_wave_state.py"]), "wave hint mismatch")
    expect("inspect spec/skill alignment and repair the drifted recovery rule" == runner.recovery_hint_for_command(["python3", "check_execution_system_governance_consistency.py"]), "governance hint mismatch")
    expect("remove baked-in full-suite health claims from durable docs and let live checks speak for current status" == runner.recovery_hint_for_command(["python3", "check_execution_system_status_freshness.py"]), "freshness hint mismatch")
    expect("inspect the failing repo smoke test and repair the drifted contract" == runner.recovery_hint_for_command(["python3", "test_any.py"]), "test hint mismatch")
    expect("inspect the command output and repair the surfaced domain" == runner.recovery_hint_for_command(["python3", "other.py"]), "default hint mismatch")
    footer = "\n".join(
        runner.summary_footer(
            runner.build_summary(
                "python3 test_any.py",
                [],
                repo_smoke_tests_status="unavailable",
                repo_smoke_tests_reason="missing tests",
            )
        )
    )
    expect("- advisory_hits: 0" in footer, footer)
    expect("- repo_smoke_tests_reason: missing tests" in footer, footer)
    expect("- recovery_hint: inspect the failing repo smoke test and repair the drifted contract" in footer, footer)

    original_discover = runner.discover_repo_tests_root
    try:
        with tempfile.TemporaryDirectory(prefix="six-layer-runner-tests-") as tmpdir:
            root = Path(tmpdir)
            plugin_link = root / "plugins" / runner.WORKSPACE.name
            plugin_link.parent.mkdir(parents=True)
            plugin_link.symlink_to(runner.WORKSPACE, target_is_directory=True)
            (root / "tests").mkdir()
            os.environ["SIX_LAYER_SOURCE_REPO_ROOT"] = str(root)
            tests_root, reason = runner.discover_repo_tests_root()
            expect(reason is None and tests_root == (root / "tests").resolve(), str((tests_root, reason)))

        os.environ["SIX_LAYER_SOURCE_REPO_ROOT"] = str(Path(tempfile.mkdtemp(prefix="six-layer-runner-missing-")))
        tests_root, reason = runner.discover_repo_tests_root()
        expect(tests_root == (Path(__file__).resolve().parents[1] / "tests").resolve() and reason is None, str((tests_root, reason)))

        os.environ["SIX_LAYER_SOURCE_REPO_ROOT"] = str(Path(__file__).resolve().parents[1])
        tests_root, reason = runner.discover_repo_tests_root()
        expect(tests_root == (Path(__file__).resolve().parents[1] / "tests").resolve() and reason is None, str((tests_root, reason)))

        with tempfile.TemporaryDirectory(prefix="six-layer-runner-dedupe-") as tmpdir:
            canonical_root = Path(tmpdir) / "canonical-root"
            override_root = Path(tmpdir) / "override-root"
            inferred_root = Path(tmpdir) / "inferred-root"
            canonical_root.mkdir()
            override_root.mkdir()
            inferred_root.mkdir()

            original_file = runner.__file__
            original_resolve = runner.Path.resolve

            def fake_resolve(self, *args, **kwargs):
                if self.name in {"override-root", "inferred-root"}:
                    return canonical_root
                if (
                    self.name == runner.WORKSPACE.name
                    and self.parent.name == "plugins"
                    and self.parent.parent.name == "canonical-root"
                ):
                    raise FileNotFoundError("synthetic missing plugin path")
                return original_resolve(self, *args, **kwargs)

            try:
                os.environ["SIX_LAYER_SOURCE_REPO_ROOT"] = str(override_root)
                runner.__file__ = str(
                    inferred_root / "plugins" / runner.WORKSPACE.name / "scripts" / "run_execution_system_checks.py"
                )
                with mock.patch.object(runner.Path, "resolve", autospec=True, side_effect=fake_resolve):
                    tests_root, reason = runner.discover_repo_tests_root()
                expect(tests_root is None, str((tests_root, reason)))
                expect(reason == "repo checkout not detected from plugin layout", str((tests_root, reason)))
            finally:
                runner.__file__ = original_file

        original_file = runner.__file__
        try:
            runner.__file__ = "run_execution_system_checks.py"
            os.environ.pop("SIX_LAYER_SOURCE_REPO_ROOT", None)
            tests_root, reason = runner.discover_repo_tests_root()
            expect(tests_root is None and reason == "repo checkout not detected from plugin layout", str((tests_root, reason)))
        finally:
            runner.__file__ = original_file
    finally:
        os.environ.pop("SIX_LAYER_SOURCE_REPO_ROOT", None)
        runner.discover_repo_tests_root = original_discover

    with mock.patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=2)):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code, summary = runner.collect_summary(print_output=True)
        expect(code == 2, buffer.getvalue())
        expect(summary.first_failing_command is not None, str(summary))
        expect("EXECUTION_SYSTEM_CHECKS_FAILED" in buffer.getvalue(), buffer.getvalue())

    with mock.patch.object(runner, "discover_repo_tests_root", return_value=(None, "repo checkout not detected from plugin layout")):
        with mock.patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code, summary = runner.collect_summary(print_output=True)
        expect(code == 0, buffer.getvalue())
        expect(summary.repo_smoke_tests_status == "skipped", str(summary))
        expect("EXECUTION_SYSTEM_REPO_SMOKE_TESTS_SKIPPED" in buffer.getvalue(), buffer.getvalue())

    with tempfile.TemporaryDirectory(prefix="six-layer-runner-fail-") as tmpdir:
        tests_root = Path(tmpdir) / "tests"
        tests_root.mkdir()

        call_count = {"value": 0}

        def fake_run(cmd, **kwargs):
            call_count["value"] += 1
            if call_count["value"] <= len(runner.CHECKS):
                return SimpleNamespace(returncode=0)
            if call_count["value"] == len(runner.CHECKS) + len(runner.ADVISORIES) + 1:
                return SimpleNamespace(returncode=1)
            return SimpleNamespace(returncode=0)

        with mock.patch.object(runner, "discover_repo_tests_root", return_value=(tests_root, None)):
            with mock.patch.object(runner.subprocess, "run", side_effect=fake_run):
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    code, summary = runner.collect_summary(print_output=True)
        expect(code == 1, buffer.getvalue())
        expect(summary.repo_smoke_tests_status == "failed", str(summary))
        expect("- repo_smoke_tests_total: 7" in buffer.getvalue(), buffer.getvalue())

    original_collect_closeout = closeout_ready.collect_summary
    original_parse_closeout = closeout_ready.parse_ledger
    try:
        closeout_ready.collect_summary = lambda print_output=False: (
            1,
            SimpleNamespace(first_failing_command="python3 failing", advisory_commands=[]),
        )
        code, output = capture_main(closeout_ready.main)
        expect(code == 1, output)
        expect("- first_failing_command: python3 failing" in output, output)

        focus = FakeActivity(
            "focus",
            fields={
                "type": "roadmap",
                "current_slice_id": "S1",
                "next_slice_id": "S2",
                "last_commit": "abc123",
            },
            list_fields={"last_validation": ["ok"]},
        )
        closeout_ready.collect_summary = lambda print_output=False: (
            0,
            SimpleNamespace(first_failing_command=None, advisory_commands=["warn-a", "warn-b"]),
        )
        closeout_ready.parse_ledger = lambda path: SimpleNamespace(get_current_focus_activity=lambda: focus)
        code, output = capture_main(closeout_ready.main)
        expect(code == 0, output)
        expect("- advisory_hits: 2" in output, output)
    finally:
        closeout_ready.collect_summary = original_collect_closeout
        closeout_ready.parse_ledger = original_parse_closeout

    with mock.patch.object(full_tests, "discover_repo_tests_root", return_value=(None, "missing tests")):
        code, output = capture_main(full_tests.main)
        expect(code == 2, output)
        expect("EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE" in output, output)

    with tempfile.TemporaryDirectory(prefix="six-layer-full-tests-") as tmpdir:
        tests_root = Path(tmpdir) / "tests"
        tests_root.mkdir()

        def fake_full_run(cmd, **kwargs):
            if cmd[-1].endswith("test_check_active_consistency.py"):
                return SimpleNamespace(returncode=1, stdout="boom\n", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(full_tests, "discover_repo_tests_root", return_value=(tests_root, None)):
            with mock.patch.object(full_tests, "repo_test_env", return_value={"PYTHONPATH": "x"}):
                with mock.patch.object(full_tests.subprocess, "run", side_effect=fake_full_run):
                    code, output = capture_main(full_tests.main)
        expect(code == 1, output)
        expect("- failed_test: active-checker-smoke" in output, output)

    print("CONSISTENCY_AND_RUNNER_HELPER_COVERAGE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
