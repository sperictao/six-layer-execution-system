# Upstream OpenClaw Runtime

## Installed Runtime Root

- Package root: `/opt/homebrew/lib/node_modules/openclaw`
- CLI entry: `/opt/homebrew/bin/openclaw`
- Main package entry: `/opt/homebrew/lib/node_modules/openclaw/dist/entry.js`

Use these upstream docs when the task is about runtime behavior rather than only
the local workspace policy.

## Workspace and Agent Basics

Read:

- `/opt/homebrew/lib/node_modules/openclaw/README.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/cli/agents.md`

Key facts:

- upstream default workspace root is `~/.openclaw/workspace` (this extracted plugin overrides the local execution root to the plugin repository root)
- upstream prompt assembly can inject multiple workspace prompt sidecars; this local plugin intentionally consolidates its prompt rules into `skills/six-layer-execution-system/SKILL.md`
- workspace-local skills live under `~/.openclaw/workspace/skills/<skill>/SKILL.md`
- multiple isolated agents can point at different workspaces and auth stores

## Sandbox and Tool Policy

Read:

- `/opt/homebrew/lib/node_modules/openclaw/docs/cli/sandbox.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/tools/multi-agent-sandbox-tools.md`

Key facts:

- OpenClaw can run tools on host or in Docker/SSH/OpenShell sandboxes
- `openclaw sandbox explain` is the primary runtime-policy inspection command
- sandbox recreation is the canonical way to apply changed sandbox config
- per-agent sandbox config overrides global defaults
- tool restrictions narrow progressively; later layers cannot re-grant earlier denials

Useful config keys:

- `agents.defaults.sandbox.*`
- `agents.list[].sandbox.*`
- `tools.allow` / `tools.deny`
- `agents.list[].tools.*`

## Embedded Agent Architecture

Read:

- `/opt/homebrew/lib/node_modules/openclaw/docs/zh-CN/pi.md`

This document is the best upstream architecture map for how OpenClaw embeds its agent runtime.

Key details captured there:

- OpenClaw embeds the Pi SDK directly through `createAgentSession()`
- runtime integrates custom tools, session storage, auth profile rotation, and prompt building
- all tools are passed as custom tools so OpenClaw can keep policy filtering and sandbox behavior consistent
- system prompt assembly includes tools, skills, docs, workspace, sandbox, reply conventions, and runtime metadata
- session state is JSONL-backed and guarded through local wrappers
- compaction safeguard and context-pruning are local Pi extensions

Important upstream path clusters from the architecture doc:

- `src/agents/pi-embedded-runner/**`
- `src/agents/pi-tools*.ts`
- `src/agents/system-prompt*.ts`
- `src/agents/tool-policy.ts`
- `src/agents/skills.ts`
- `src/agents/sandbox.ts`
- `src/agents/tools/**`

The installed package is already compiled, so the local file names differ under `dist/`,
but the architecture document preserves the conceptual source layout.

## Security Model Anchors

From the installed README and docs:

- main-session tools default to host execution unless sandboxing is enabled
- non-main sessions can be sandboxed with `mode: "non-main"` or stricter
- sandbox defaults typically allow coding/file tools and deny gateway/browser/channel families

When the task touches security posture, combine:

1. local config snapshot from `references/local-install.md`
2. local workspace rules from `references/workspace-execution-system.md`
3. upstream sandbox/tool docs from the paths above
