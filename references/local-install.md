# Local OpenClaw Install Snapshot

## Scope

This reference records the machine-local OpenClaw install facts that were extracted on 2026-03-26.

Treat these as a baseline snapshot. Re-run `python3 ../scripts/inspect_openclaw_execution_system.py`
when you need current facts.

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
- Default runtime root: `/Users/erictao/source/repos/six-layer-execution-system`
- Workspace-local skills are intentionally omitted from this minimal repository copy.
- Agent state root: `/Users/erictao/.openclaw/agents`
- Logs: `/Users/erictao/.openclaw/logs`
- Credentials: `/Users/erictao/.openclaw/credentials`

## Redacted Config Snapshot

The live config is token-bearing. Never quote it verbatim without redaction.

Current high-level shape:

- `agents.defaults.model.primary`: `packycode/gpt-5.4-xhigh`
- `agents.defaults.model.fallbacks`: `packycode/gpt-5.2-xhigh`
- `agents.defaults.workspace`: `/Users/erictao/source/repos/six-layer-execution-system`
- `agents.defaults.compaction.mode`: `safeguard`
- `skills.load.extraDirs`: `[]`
- `skills.install.nodeManager`: `npm`
- `gateway.mode`: `local`
- `gateway.bind`: `loopback`
- `gateway.port`: `18789`
- `gateway.auth.mode`: `token`
- `gateway.controlUi.allowedOrigins`: Tauri localhost + local dev origins
- enabled channels observed in config: `feishu`, `qqbot`

Model/provider families present in the redacted snapshot:

- `kimi`
- `packycode`
- `qclaw`
- `wong`

## Workspace Top-Level Files

Key execution files currently present:

- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `TOOLS.md`
- `ACTIVE.md`
- `HEARTBEAT.md`
- `MEMORY.md`
- `SESSION-STATE.md`
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

## Execution-System-Specific Workspace Assets

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

## Upstream Runtime Facts That Matter Locally

From the installed package:

- Workspace root defaults to `~/.openclaw/workspace`.
- Prompt files injected into the workspace include `AGENTS.md`, `SOUL.md`, `TOOLS.md`.
- Workspace-local skills live under `~/.openclaw/workspace/skills/<skill>/SKILL.md`.
- Host execution is the default for main-session tools unless sandbox mode is enabled.
- Non-main sessions can be routed into Docker/SSH/OpenShell sandboxes depending on config.
