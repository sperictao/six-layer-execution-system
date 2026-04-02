# Local Runtime Reference

## Scope

This reference records only the machine-local install facts that still matter to this repository.

Treat these as a minimal baseline snapshot. Re-run `python3 ../scripts/inspect_openclaw_execution_system.py`
when you need current facts instead of expanding this file into a full environment dump.

## Installed Binary and Package

- CLI binary: `/opt/homebrew/bin/openclaw`
- Reported version: `OpenClaw 2026.3.23-2 (7ffe7e4)`
- npm global root: `/opt/homebrew/lib/node_modules`
- Installed package root: `/opt/homebrew/lib/node_modules/openclaw`
- CLI bootstrap entry: `/opt/homebrew/bin/openclaw`
- Package entry module: `/opt/homebrew/lib/node_modules/openclaw/dist/entry.js`

## Local State Root

- State root: `/Users/erictao/.openclaw`
- Main config: `/Users/erictao/.openclaw/openclaw.json`
- Default runtime root: `<plugin-root>`

Do not persist token-bearing config details, provider lists, channel choices, or model selections here.
Inspect them live only when a task truly depends on them.

## Repository Runtime Surface

Key execution files currently present:

- `skills/six-layer-execution-system/SKILL.md`
- `ACTIVE.md`
- `docs/execution-system-spec-v1.md`
- `docs/execution-system-maintenance-guardrails.md`
- `docs/execution-system-testing-inventory.md`

Key execution directories currently present:

- `contracts/`
- `roadmaps/`
- `tasks/`
- `decisions/`
- `memory/`
- `references/`
- `scripts/`
- `skills/`

## Execution-System-Owned Assets

Docs:

- `docs/execution-system-spec-v1.md`
- `docs/execution-system-maintenance-guardrails.md`
- `docs/execution-system-testing-inventory.md`
- `docs/execution-system-decomposition-upgrade-plan.md`
- `docs/execution-system-spec-v1-acceptance-checklist.md`

Roadmaps:

- `roadmaps/execution-system-spec-v1-roadmap.md`
- `roadmaps/execution-system-testing-roadmap.md`
- `roadmaps/execution-system-decomposition-upgrade-roadmap.md`

Tasks:

- `tasks/execution-system-spec-v1-tasks.md`
- `tasks/execution-system-testing-tasks.md`
- `tasks/execution-system-decomposition-upgrade-tasks.md`

Scripts:

- ACTIVE parser/checkers
- dependency/parallel-wave checkers
- governance/status checkers
- closeout + notification scripts
- unified check runner
- unified full-test runner

## External Runtime Facts That Matter Locally

From the installed package:

- Upstream OpenClaw still defaults its workspace root to `~/.openclaw/workspace`, but this extracted plugin overrides the local execution root to the plugin repository root via `SIX_LAYER_WORKSPACE`.
- Upstream OpenClaw historically injected several workspace prompt sidecars; this extracted plugin instead consolidates local prompt rules into `skills/six-layer-execution-system/SKILL.md`.
- In upstream layout, workspace-local skills live under `~/.openclaw/workspace/skills/<skill>/SKILL.md`; in this extracted plugin, local skills live under `<plugin-root>/skills/<skill>/SKILL.md`.
- Host execution is the default for main-session tools unless sandbox mode is enabled.
- Non-main sessions can be routed into Docker/SSH/OpenShell sandboxes depending on config.
