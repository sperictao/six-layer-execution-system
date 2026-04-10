# Agent Runtime Reference

## Supported Agent Hosts

This plugin is designed to work with any agent system that supports plugin directories
with skill-based prompt rules. Verified targets:

- **Claude Code** — loads `skills/six-layer-execution-system/SKILL.md` as the prompt authority
- **Codex** — discovers the plugin via `.codex-plugin/plugin.json`
- **OpenAI Agents** — uses `agents/openai.yaml` for interface metadata

---

## Plugin Installation

Copy the entire `six-layer-execution-system/` directory into the target agent's plugin
directory. No additional runtime dependencies are required.

After installation, verify the environment:

```bash
python3 scripts/inspect_execution_system.py --format markdown
python3 scripts/run_execution_checks.py checks --timeout 60
```

---

## Prompt Authority

`skills/six-layer-execution-system/SKILL.md` is the sole prompt-rule source of truth.
All behavioral rules, recovery sequences, and closeout handoff protocols are defined there.

In Claude Code, skills are loaded from the `skills/<skill-name>/SKILL.md` path within
the plugin root. The root-level `SKILL.md` serves as a short entry pointer.

---

## Runtime Root Resolution

All scripts resolve their workspace root in this order:

1. `SIX_LAYER_WORKSPACE` environment variable (if set)
2. `SIX_LAYER_REPO_ROOT` environment variable (if set)
3. Plugin root directory (default — works in all standalone deployments)

| Variable | Default | Purpose |
|---|---|---|
| `SIX_LAYER_WORKSPACE` | `<plugin-root>` | Plugin workspace root |
| `SIX_LAYER_REPO_ROOT` | `<plugin-root>` | Repo root for path resolution |
| `SIX_LAYER_STATE_ROOT` | `<plugin-root>/local-state` | Local state directory |

No environment variable changes are needed for standard standalone deployment.

---

## Full-Test Availability

`scripts/run_execution_system_full_tests.py` requires the source checkout `tests/`
directory. When running from a standalone plugin copy, it reports `unavailable` — this
is expected and not a runtime failure.

Plugin-local checkers (`run_execution_checks.py checks`) are always available and do
not require the source checkout.
