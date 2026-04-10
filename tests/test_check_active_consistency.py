#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from test_workspace_clone import cloned_workspace, init_git_repo, workspace_env


def run_checker(workspace: Path, active_path: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(workspace / "scripts" / "check_active_consistency.py"), str(active_path)],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def write_case(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def expect_ok(name: str, proc: subprocess.CompletedProcess[str]) -> None:
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass, got {proc.stdout}{proc.stderr}")


def expect_fail(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail")
    output = proc.stdout + proc.stderr
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def extract_current_focus(original: str) -> str:
    marker = "- current_focus_activity_id: `"
    start = original.index(marker) + len(marker)
    end = original.index("`", start)
    return original[start:end]


def extract_activity_type(original: str, activity_id: str) -> str:
    return extract_focus_scalar(original, activity_id, "type")


def extract_focus_scalar(original: str, activity_id: str, field: str) -> str:
    anchor = f"### Activity: {activity_id}\n"
    start = original.index(anchor)
    needle = f"- {field}: `"
    field_start = original.index(needle, start) + len(needle)
    field_end = original.index("`", field_start)
    return original[field_start:field_end]


def replace_focus_scalar(original: str, activity_id: str, field: str, value: str) -> str:
    anchor = f"### Activity: {activity_id}\n"
    start = original.index(anchor)
    needle = f"- {field}: `"
    field_start = original.index(needle, start) + len(needle)
    field_end = original.index("`", field_start)
    return original[:field_start] + value + original[field_end:]


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        original = (workspace / "ACTIVE.md").read_text(encoding="utf-8")
        real_focus_id = extract_current_focus(original)
        focus_id = real_focus_id
        if extract_activity_type(original, focus_id) != "roadmap":
            for activity_id in (
                "execution-system-spec-v1",
                "execution-system-decomposition-upgrade",
                "active-ledger-v2",
            ):
                if f"### Activity: {activity_id}\n" in original:
                    focus_id = activity_id
                    break

        portable_source = original
        if focus_id != real_focus_id:
            portable_source = portable_source.replace(
                f"- current_focus_activity_id: `{real_focus_id}`",
                f"- current_focus_activity_id: `{focus_id}`",
                1,
            )
            portable_source = portable_source.replace(
                f"- default_reply_activity_id: `{real_focus_id}`",
                f"- default_reply_activity_id: `{focus_id}`",
                1,
            )
        portable_source = replace_focus_scalar(portable_source, focus_id, "path", ".")

        with tempfile.TemporaryDirectory(prefix="active-check-") as tmpdir:
            tmp = Path(tmpdir)
            no_git = write_case(tmp / "ACTIVE-no-git.md", portable_source)
            expect_ok("portable-no-git", run_checker(workspace, no_git, env))

        baseline_commit = init_git_repo(workspace)
        test_source = replace_focus_scalar(portable_source, focus_id, "last_commit", baseline_commit)

        source_doc = extract_focus_scalar(test_source, focus_id, "source_doc")
        roadmap_doc = extract_focus_scalar(test_source, focus_id, "roadmap_doc")

        with tempfile.TemporaryDirectory(prefix="active-check-") as tmpdir:
            tmp = Path(tmpdir)

            happy = write_case(tmp / "ACTIVE-happy.md", test_source)
            expect_ok("happy-path", run_checker(workspace, happy, env))

            missing_source = write_case(
                tmp / "ACTIVE-missing-source.md",
                test_source.replace(
                    f"- source_doc: `{source_doc}`\n",
                    "",
                    1,
                ),
            )
            expect_fail(
                "missing-source-doc",
                run_checker(workspace, missing_source, env),
                f"focus:{focus_id}: missing `source_doc`",
            )

            broken_roadmap = write_case(
                tmp / "ACTIVE-broken-roadmap.md",
                test_source.replace(
                    f"- roadmap_doc: `{roadmap_doc}`",
                    f"- roadmap_doc: `{workspace / 'roadmaps' / 'does-not-exist.md'}`",
                    1,
                ),
            )
            expect_fail(
                "broken-roadmap-doc",
                run_checker(workspace, broken_roadmap, env),
                f"focus:{focus_id}: `roadmap_doc` points to missing file",
            )

    print("ACTIVE_CHECKER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
