#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import scripts.check_active_wave_state as check_active_wave_state
import scripts.check_execution_system_governance_consistency as governance
import scripts.check_execution_system_status_freshness as status_freshness
import scripts.check_oversized_migration_slices as oversized_slices
import scripts.check_parallel_safety as parallel_safety
import scripts.check_task_dependency_graph as dependency_graph
import scripts.check_task_slice_schema as task_slice_schema


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def capture_main(fn, argv: list[str]) -> tuple[int, str]:
    buffer = io.StringIO()
    old_argv = sys.argv[:]
    try:
        sys.argv = argv
        with contextlib.redirect_stdout(buffer):
            code = int(fn())
    finally:
        sys.argv = old_argv
    return code, buffer.getvalue()


def main() -> int:
    schema_block = [
        "- phase_id:",
        "- rollback_strategy:",
    ]
    schema_fields = task_slice_schema.extract_fields(schema_block)
    expect(schema_fields["phase_id"] == "", str(schema_fields))
    expect(schema_fields["rollback_strategy"] == "", str(schema_fields))
    expect(task_slice_schema.is_in_scope_slice("#### Slice X - Demo", {"phase_id": "P1"}), "phase_id slice should be in scope")
    expect(task_slice_schema.is_in_scope_slice("#### Slice X - Demo", {"rollback_strategy": "revert"}), "rollback slice should be in scope")
    expect(not task_slice_schema.is_in_scope_slice("### Not A Slice", {"phase_id": "P1"}), "non-slice heading should be out of scope")
    with tempfile.TemporaryDirectory(prefix="six-layer-schema-") as tmpdir:
        task_doc = Path(tmpdir) / "tasks.md"
        task_doc.write_text(
            "\n".join(
                [
                    "#### Slice X - Missing phase",
                    "- rollback_strategy: `revert`",
                    "",
                    "#### Slice Y - Missing rollback",
                    "- phase_id: `PH-1`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        problems = task_slice_schema.validate_task_doc(task_doc)
        expect(any("missing `phase_id`" in item for item in problems), str(problems))
        expect(any("missing `rollback_strategy`" in item for item in problems), str(problems))
        code, output = capture_main(task_slice_schema.main, ["check_task_slice_schema.py", str(task_doc)])
        expect(code == 1, output)
        expect("TASK_SLICE_SCHEMA_CHECK_FAILED" in output, output)

    dep_values = dependency_graph.parse_dep_values("`DX-E.E1` | E2 | invalid | none")
    expect(dep_values == ["E1", "E2", "INVALID:invalid"], str(dep_values))
    with tempfile.TemporaryDirectory(prefix="six-layer-deps-") as tmpdir:
        task_doc = Path(tmpdir) / "deps.md"
        task_doc.write_text(
            "\n".join(
                [
                    "#### Not a slice",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "  - ignored",
                    "- depends_on:",
                    "  - E1",
                    "",
                    "#### Slice E1 - Missing deps",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "",
                    "#### Slice E2 - Bad deps",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "- depends_on:",
                    "  - invalid",
                    "  - E2",
                    "  - E9",
                    "",
                    "#### Slice E3 - Cycle A",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "- depends_on:",
                    "  - E4",
                    "",
                    "#### Slice E4 - Cycle B",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "- depends_on:",
                    "  - E3",
                ]
            ),
            encoding="utf-8",
        )
        problems = dependency_graph.validate_task_doc(task_doc)
        expect(any("missing `depends_on`" in item for item in problems), str(problems))
        expect(any("invalid dependency reference `invalid`" in item for item in problems), str(problems))
        expect(any("depends on itself" in item for item in problems), str(problems))
        expect(any("depends on unknown slice `E9`" in item for item in problems), str(problems))
        expect(any("dependency cycle" in item for item in problems), str(problems))
        code, output = capture_main(dependency_graph.main, ["check_task_dependency_graph.py", str(task_doc)])
        expect(code == 1, output)
        expect("TASK_DEPENDENCY_GRAPH_CHECK_FAILED" in output, output)

    parallel_fields = parallel_safety.extract_fields(["- shared_write_targets:", "  - file1", "  - file2"])
    expect(parallel_fields["shared_write_targets"] == "file1 | file2", str(parallel_fields))
    expect(parallel_safety.parse_list_field("") == [], "empty list field should be empty")
    expect(parallel_safety.parse_list_field("file1 | none | file2") == ["file1", "file2"], "list parser should drop none")
    with tempfile.TemporaryDirectory(prefix="six-layer-parallel-") as tmpdir:
        task_doc = Path(tmpdir) / "parallel.md"
        task_doc.write_text(
            "\n".join(
                [
                    "#### Not a slice",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "  - ignored",
                    "",
                    "#### Slice E1 - Invalid bool",
                    "- parallel_safe: `maybe`",
                    "- shared_write_targets:",
                    "",
                    "#### Slice E2 - Missing targets",
                    "- parallel_safe: `true`",
                    "",
                    "#### Slice E3 - True with targets",
                    "- parallel_safe: `true`",
                    "- shared_write_targets:",
                    "  - file1",
                    "",
                    "#### Slice E4 - False without targets",
                    "- parallel_safe: `false`",
                    "- shared_write_targets: `none`",
                ]
            ),
            encoding="utf-8",
        )
        problems = parallel_safety.validate_task_doc(task_doc)
        expect(any("`parallel_safe` must be `true` or `false`" in item for item in problems), str(problems))
        expect(any("missing `shared_write_targets`" in item for item in problems), str(problems))
        expect(any("conflicts with non-empty `shared_write_targets`" in item for item in problems), str(problems))
        expect(any("should explain the write surface" in item for item in problems), str(problems))
        code, output = capture_main(parallel_safety.main, ["check_parallel_safety.py", str(task_doc)])
        expect(code == 1, output)
        expect("PARALLEL_SAFETY_CHECK_FAILED" in output, output)

    class WaveActivity:
        def __init__(self, fields: dict[str, object]):
            self.activity_id = fields.get("activity_id", "wave") if isinstance(fields.get("activity_id"), str) else "wave"
            self.heading = self.activity_id
            self._fields = fields

        def scalar(self, key: str):
            value = self._fields.get(key)
            return value if isinstance(value, str) else None

        def items(self, key: str):
            value = self._fields.get(key)
            return list(value) if isinstance(value, list) else []

    expect(not check_active_wave_state.has_any_wave_state(WaveActivity({"activity_id": "none"})), "no wave state should be false")
    expect(
        check_active_wave_state.has_any_wave_state(WaveActivity({"activity_id": "scalar", "execution_mode": "serial"})),
        "scalar wave state should be true",
    )
    expect(
        check_active_wave_state.has_any_wave_state(WaveActivity({"activity_id": "list", "ready_slices": ["A"]})),
        "list wave state should be true",
    )

    class WaveLedger:
        def __init__(self, activities):
            self._activities = activities

        def list_activities(self):
            return list(self._activities)

    original_parse_wave = check_active_wave_state.parse_ledger
    try:
        check_active_wave_state.parse_ledger = lambda path: WaveLedger(
            [
                WaveActivity({"activity_id": "bad-type", "type": "waiting", "execution_mode": "parallel-wave"}),
                WaveActivity({"activity_id": "bad-mode", "type": "roadmap", "execution_mode": "weird"}),
                WaveActivity({"activity_id": "serial", "type": "roadmap", "execution_mode": "serial"}),
                WaveActivity({"activity_id": "missing-fields", "type": "roadmap", "execution_mode": "parallel-wave"}),
            ]
        )
        problems = check_active_wave_state.validate_task_doc(Path("/tmp/ACTIVE.md"))
        expect(any("only allowed on roadmap activities" in item for item in problems), str(problems))
        expect(any("must be `serial` or `parallel-wave`" in item for item in problems), str(problems))
        expect(any("should not be present when `execution_mode` is `serial`" in item for item in problems), str(problems))
        expect(any("missing `current_wave_id`" in item for item in problems), str(problems))
        expect(any("missing list `integration_step`" in item for item in problems), str(problems))
        expect(any("must expose at least one" in item for item in problems), str(problems))
        code, output = capture_main(check_active_wave_state.main, ["check_active_wave_state.py", "/tmp/ACTIVE.md"])
        expect(code == 1, output)
        expect("ACTIVE_WAVE_STATE_CHECK_FAILED" in output, output)
    finally:
        check_active_wave_state.parse_ledger = original_parse_wave

    oversized_fields, oversized_lists = oversized_slices.extract_fields(["- scope:", "- done_definition:"])
    expect(oversized_fields["scope"] == "", str(oversized_fields))
    expect(oversized_lists["scope"] == [], str(oversized_lists))
    expect(not oversized_slices.is_in_scope_slice("### Not Slice", {"phase_id": "P1"}), "invalid heading should be out of scope")
    expect(not oversized_slices.is_in_scope_slice("#### Slice 1A - Subslice", {"phase_id": "P1"}), "subslice token should be out of scope")
    expect(oversized_slices.is_in_scope_slice("#### Slice P1 - Broad", {"phase_id": "P1"}), "phase slice should be in scope")
    reasons = oversized_slices.advisory_reasons(
        "#### Slice P1 - Broad",
        {
            "scope": ["a", "b", "c", "d", "e"],
            "done_definition": ["x", "y"],
            "target_files": ["f1", "f2", "f3"],
        },
    )
    expect(any("heading uses a broad phase-level slice id" in item for item in reasons), str(reasons))
    expect(any("scope has 5 entries" in item for item in reasons), str(reasons))
    with tempfile.TemporaryDirectory(prefix="six-layer-oversized-") as tmpdir:
        advisory_doc = Path(tmpdir) / "oversized.md"
        advisory_doc.write_text(
            "\n".join(
                [
                    "#### Slice P1 - Broad slice",
                    "- phase_id: `PH-1`",
                    "- scope:",
                    "  - a",
                    "  - b",
                    "  - c",
                    "  - d",
                    "  - e",
                    "- done_definition:",
                    "  - x",
                    "  - y",
                    "- target_files:",
                    "  - f1",
                    "  - f2",
                    "  - f3",
                ]
            ),
            encoding="utf-8",
        )
        warnings = oversized_slices.check_task_doc(advisory_doc)
        expect(len(warnings) == 1, str(warnings))
        code, output = capture_main(oversized_slices.main, ["check_oversized_migration_slices.py", str(advisory_doc)])
        expect(code == 0, output)
        expect("OVERSIZED_MIGRATION_SLICE_ADVISORY" in output, output)

        ok_doc = Path(tmpdir) / "ok.md"
        ok_doc.write_text("#### Slice X - Focused\n- phase_id: `PH-1`\n", encoding="utf-8")
        code, output = capture_main(oversized_slices.main, ["check_oversized_migration_slices.py", str(ok_doc)])
        expect(code == 0, output)
        expect("OVERSIZED_MIGRATION_SLICE_OK" in output, output)

    with tempfile.TemporaryDirectory(prefix="six-layer-freshness-") as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "docs").mkdir()
        active_path = workspace / "ACTIVE.md"
        active_path.write_text("run_execution_system_full_tests.py failed: 1\n", encoding="utf-8")
        problems = status_freshness.find_problems(workspace, active_path)
        expect(len(problems) == 1 and "stale suite-health claim" in problems[0], str(problems))

        code, output = capture_main(status_freshness.main, ["check_execution_system_status_freshness.py", str(workspace)])
        expect(code == 1, output)
        expect("ACTIVE.md:1: stale suite-health claim" in output, output)

        active_path.write_text("clean\n", encoding="utf-8")
        code, output = capture_main(status_freshness.main, ["check_execution_system_status_freshness.py", str(workspace)])
        expect(code == 1, output)
        expect("docs/execution-system-testing-inventory.md: missing required file" in output, output)

    problems: list[str] = []
    governance.expect_contains("hello", "missing", "scope", problems)
    expect(problems == ["scope: missing `missing`"], str(problems))
    original_spec = governance.SPEC
    original_roadmap = governance.ROADMAP
    original_tasks = governance.TASKS
    original_active = governance.ACTIVE
    original_acceptance = governance.ACCEPTANCE
    original_skill = governance.SKILL
    try:
        with tempfile.TemporaryDirectory(prefix="six-layer-governance-") as tmpdir:
            root = Path(tmpdir)
            files = {
                "spec.md": "",
                "roadmap.md": "",
                "tasks.md": "",
                "active.md": "",
                "acceptance.md": "AGENTS.md\n",
                "skill.md": "",
            }
            for name, text in files.items():
                (root / name).write_text(text, encoding="utf-8")
            governance.SPEC = root / "spec.md"
            governance.ROADMAP = root / "roadmap.md"
            governance.TASKS = root / "tasks.md"
            governance.ACTIVE = root / "active.md"
            governance.ACCEPTANCE = root / "acceptance.md"
            governance.SKILL = root / "skill.md"
            code, output = capture_main(governance.main, ["check_execution_system_governance_consistency.py"])
            expect(code == 1, output)
            expect("EXECUTION_SYSTEM_GOVERNANCE_CONSISTENCY_FAILED" in output, output)
            expect("acceptance: deleted prompt files still referenced" in output, output)
        pass
    finally:
        governance.SPEC = original_spec
        governance.ROADMAP = original_roadmap
        governance.TASKS = original_tasks
        governance.ACTIVE = original_active
        governance.ACCEPTANCE = original_acceptance
        governance.SKILL = original_skill

    print("CHECKER_HELPER_COVERAGE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
