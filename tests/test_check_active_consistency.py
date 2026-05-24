#!/usr/bin/env python3
from __future__ import annotations

import subprocess
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


def expect_ok(name: str, proc: subprocess.CompletedProcess[str]) -> None:
    if proc.returncode != 0:
        raise AssertionError(f"{name} should pass, got {proc.stdout}{proc.stderr}")


def expect_fail(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    if proc.returncode == 0:
        raise AssertionError(f"{name} should fail")
    output = proc.stdout + proc.stderr
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def extract_current_focus(active_text: str) -> str:
    """Extract current_focus_activity_id from v3 ACTIVE.md meta."""
    marker = "- current_focus_activity_id: `"
    start = active_text.index(marker) + len(marker)
    end = active_text.index("`", start)
    return active_text[start:end]


def read_card(workspace: Path, activity_id: str) -> str:
    """Read the activity card from activities/<id>/card.md."""
    card_path = workspace / "activities" / activity_id / "card.md"
    return card_path.read_text(encoding="utf-8") if card_path.exists() else ""


def extract_card_scalar(card_text: str, field: str) -> str:
    """Extract a scalar value from a card.md file."""
    import re
    m = re.search(rf"^- {field}: `([^`]+)`$", card_text, re.MULTILINE)
    if m:
        return m.group(1)
    m = re.search(rf"^- {field}: (.+)$", card_text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    raise ValueError(f"field {field} not found in card")


def replace_card_scalar(card_text: str, field: str, value: str) -> str:
    """Replace a scalar value in a card.md text."""
    import re
    pattern = rf"^(- {field}: )`[^`]+`"
    repl = rf"\1`{value}`"
    new = re.sub(pattern, repl, card_text, count=1, flags=re.MULTILINE)
    if new == card_text:
        pattern = rf"^(- {field}: ).+$"
        repl = rf"\1{value}"
        new = re.sub(pattern, repl, card_text, count=1, flags=re.MULTILINE)
    return new


def write_card(workspace: Path, activity_id: str, card_text: str) -> Path:
    """Write updated card.md."""
    card_path = workspace / "activities" / activity_id / "card.md"
    card_path.write_text(card_text, encoding="utf-8")
    return card_path


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        active_path = workspace / "ACTIVE.md"
        active_text = active_path.read_text(encoding="utf-8")
        real_focus_id = extract_current_focus(active_text)

        # Find a roadmap activity for testing (v3: check index table)
        focus_id = real_focus_id
        card_text = read_card(workspace, focus_id)
        if "type: `roadmap`" not in card_text:
            for activity_id in (
                "execution-system-spec-v1",
                "execution-system-decomposition-upgrade",
                "active-ledger-v2",
            ):
                alt_card = read_card(workspace, activity_id)
                if alt_card and "type: `roadmap`" in alt_card:
                    focus_id = activity_id
                    card_text = alt_card
                    break

        # Build portable ACTIVE.md with focus switched if needed
        portable_active = active_text
        if focus_id != real_focus_id:
            portable_active = portable_active.replace(
                f"- current_focus_activity_id: `{real_focus_id}`",
                f"- current_focus_activity_id: `{focus_id}`",
                1,
            )
            portable_active = portable_active.replace(
                f"- default_reply_activity_id: `{real_focus_id}`",
                f"- default_reply_activity_id: `{focus_id}`",
                1,
            )
        active_path.write_text(portable_active, encoding="utf-8")

        # Set path=. in the test card
        test_card = replace_card_scalar(card_text, "path", ".")
        write_card(workspace, focus_id, test_card)

        expect_ok("portable-no-git", run_checker(workspace, active_path, env))

        baseline_commit = init_git_repo(workspace)
        test_card2 = replace_card_scalar(test_card, "last_commit", baseline_commit)
        write_card(workspace, focus_id, test_card2)

        source_doc = extract_card_scalar(test_card2, "source_doc")
        roadmap_doc = extract_card_scalar(test_card2, "roadmap_doc")

        expect_ok("happy-path", run_checker(workspace, active_path, env))

        # Test missing source_doc
        missing_source_card = test_card2.replace(
            f"- source_doc: `{source_doc}`\n",
            "",
            1,
        )
        write_card(workspace, focus_id, missing_source_card)
        expect_fail(
            "missing-source-doc",
            run_checker(workspace, active_path, env),
            f"focus:{focus_id}: missing `source_doc`",
        )

        # Restore card
        write_card(workspace, focus_id, test_card2)

        # Test broken roadmap_doc
        broken_card = replace_card_scalar(test_card2, "roadmap_doc", "does-not-exist.md")
        write_card(workspace, focus_id, broken_card)
        expect_fail(
            "broken-roadmap-doc",
            run_checker(workspace, active_path, env),
            f"focus:{focus_id}: `roadmap_doc` points to missing file",
        )

    print("ACTIVE_CHECKER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
