#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE))

from scripts.run_execution_system_checks import collect_summary

CHECKS = [
    (
        "execution-system-suite",
        ["python3", str(WORKSPACE / "scripts/run_execution_system_checks.py")],
    ),
    (
        "focus-first",
        ["python3", str(WORKSPACE / "scripts/validate_focus_first.py")],
    ),
    ("parser-pycompile", ["py_compile", str(WORKSPACE / "scripts/active_ledger.py")]),
    ("focus-switch-tool-pycompile", ["py_compile", str(WORKSPACE / "scripts/set_focus_activity.py")]),
]


def run_check(name: str, cmd: list[str]) -> tuple[str, str]:
    if name == "execution-system-suite":
        code, summary = collect_summary(print_output=False)
        output_lines = [
            f"EXECUTION_SYSTEM_SUMMARY_STATUS:{summary.hard_fail_status}",
            f"first_failing_command={summary.first_failing_command or 'none'}",
            f"advisory_hits={len(summary.advisory_commands)}",
        ]
        for advisory in summary.advisory_commands:
            output_lines.append(f"advisory_command={advisory}")
        output = "\n".join(output_lines)
        return ("ok" if code == 0 else "fail"), output

    if name in {"parser-pycompile", "focus-switch-tool-pycompile"}:
        try:
            with tempfile.NamedTemporaryFile(prefix=f"{name}-", suffix=".pyc") as compiled:
                py_compile.compile(cmd[1], cfile=compiled.name, doraise=True)
            return "ok", f"py_compile ok: {cmd[1]}"
        except py_compile.PyCompileError as exc:
            return "fail", str(exc)

    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        return "ok", out.strip()
    except subprocess.CalledProcessError as exc:
        output = exc.output.strip()
        if exc.returncode == 2 and output.startswith("FOCUS_VALIDATION_POLICY_GATE"):
            return "policy_gate", output
        return "fail", output


def main() -> int:
    failures = []
    policy_gates = []
    for name, cmd in CHECKS:
        result, output = run_check(name, cmd)
        status = "OK" if result == "ok" else "POLICY_GATE" if result == "policy_gate" else "FAIL"
        print(f"[{status}] {name}")
        if output:
            for line in output.splitlines():
                print(f"  {line}")
        if result == "fail":
            failures.append(name)
        elif result == "policy_gate":
            policy_gates.append(name)

    if failures:
        print("ACTIVE_LEDGER_V2_ACCEPTANCE_FAILED")
        print("- failures: " + ", ".join(failures))
        return 1

    if policy_gates:
        print("ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES")
        print("- policy_gates: " + ", ".join(policy_gates))
        return 0

    print("ACTIVE_LEDGER_V2_ACCEPTANCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
