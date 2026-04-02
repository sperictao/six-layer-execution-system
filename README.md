# Six-Layer Execution System Plugin Repo

这个仓库现在是一个插件打包仓库，真正的 self-contained 插件位于：

- `plugins/six-layer-execution-system/`

该目录包含 execution-system 的运行态真相、脚本、技能、资源和插件 manifest。设计目标是把这个目录整体复制到另一台机器的 Codex 插件目录后即可使用，不再依赖当前仓库根目录。

## Development Layout

- 插件本体：`plugins/six-layer-execution-system/`
- 可选 repo-local marketplace：`.agents/plugins/marketplace.json`
- 根目录只保留 git 历史和分发壳层

## Canonical Entrypoints

从 `plugins/six-layer-execution-system/` 目录运行：

```bash
python3 scripts/inspect_execution_system.py --format markdown
python3 scripts/run_execution_checks.py checks --timeout 60
python3 scripts/run_execution_checks.py full-tests --timeout 60
```

说明：
- `checks` 始终可用；如果当前是完整 source checkout，它还会追加运行仓库根 `tests/` 下的 repo smoke tests。
- `full-tests` 现在依赖仓库根 `tests/`。把 `plugins/six-layer-execution-system/` 单独复制出去后，该入口会明确返回 `unavailable`，不再承诺完整测试套件可运行。

## Install Shape

建议把 `plugins/six-layer-execution-system/` 整个目录复制到目标机器的 Codex 插件目录中，并按目标环境需要选择是否登记 marketplace。
