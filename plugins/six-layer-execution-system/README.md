# Six-Layer Execution System

这个目录本身就是一个可单独复制、可发现、可运行的 Codex execution-system 插件。
把整个目录复制到另一台机器的 Codex 插件目录后，`ACTIVE.md`、脚本、技能、资源和插件元数据会一起随迁。

## Install And Verify

1. 复制整个 `six-layer-execution-system/` 目录到目标机器的 Codex 插件目录。
2. 如果需要在当前仓库内演示或调试 marketplace，再使用仓库根的 `.agents/plugins/marketplace.json`；它不是插件运行前提。
3. 进入插件目录后，按 `AGENTS.md` -> `ACTIVE.md` -> `skills/six-layer-execution-system/SKILL.md` 的顺序恢复上下文。
4. 首次校验优先运行：
   - `python3 scripts/inspect_execution_system.py --format markdown`
   - `python3 scripts/run_execution_checks.py checks --timeout 60`

## Runtime Truth

- 插件根目录控制文件、`contracts/`、`docs/`、`roadmaps/`、`tasks/`、`decisions/`、`memory/` 共同构成 execution-system 本体。
- `ACTIVE.md` 是唯一 live runtime truth。
- `references/` 只保存辅助参考，不替代运行态真相。
- `scripts/` 提供 inspect、checker、closeout、notification 与 acceptance 入口。
- repo-local 开发测试位于源仓库根 `tests/`，不随插件目录单独分发。

## First Entry Points

- inspect:
  - `python3 scripts/inspect_execution_system.py --format markdown`
- checks:
  - `python3 scripts/run_execution_checks.py checks --timeout 60`
- full tests:
  - `python3 scripts/run_execution_checks.py full-tests --timeout 60`

说明：
- `checks` 始终可用；它会先跑插件内 checker，再在可检测到源仓库根 `tests/` 时追加 repo smoke tests。
- `full-tests` 依赖源仓库 checkout 的根 `tests/` 目录；单独复制插件目录时，该入口会返回 `unavailable`，这是当前设计边界。

如果需要直接调底层入口，也可以使用：

```bash
python3 scripts/inspect_openclaw_execution_system.py --format markdown
python3 scripts/run_local_execution_checks.py checks --timeout 60
python3 scripts/run_local_execution_checks.py full-tests --timeout 60
```

## Packaging Metadata

- `.codex-plugin/plugin.json`
- `AGENTS.md`
- `skills/six-layer-execution-system/SKILL.md`
- `SKILL.md`
- `agents/openai.yaml`

这些文件服务于插件发现与交互，但不构成运行态真相。

## Portability

- 所有运行时脚本默认以当前插件根为工作根。
- `ACTIVE.md` 中的运行时路径使用 `<plugin-root>` 占位，复制到其它机器后无需改写为新的绝对路径。
- 如需校验当前环境是否完整，优先运行 `python3 scripts/run_execution_checks.py checks --timeout 60`。
