# Six-Layer Execution System Code Wiki

## 1. 项目概览

`six-layer-execution-system` 是一个可独立复制、可安装、可运行的 Codex 插件，用来承载并校验一套 **focus-first 六层执行系统**。它不是传统业务应用，而是一套“执行协议 + 运行账本 + 校验脚本 + closeout/handoff 工具链”。

这套系统的核心目标是：

- 用 `ACTIVE.md` 作为唯一运行态真相，回答“现在在做什么”。
- 用每个 `activities/<activity-id>/` 目录内的 contract / roadmap / tasks / decisions / memory 分层承载稳定约束、计划、切片设计、决策与恢复信息。
- 用脚本把“文档规范”升级为“可执行、可验证、可恢复”的执行系统。
- 让插件目录本身即可迁移到另一台机器使用，不依赖仓库根的开发资产。

## 2. 技术栈与运行基础

- 语言：Python 3
- 运行依赖：Python 标准库、Git 命令行
- 主要资产：Markdown 文档、Python 脚本、Codex 插件元数据
- 分发形态：复制 `plugins/six-layer-execution-system/` 整个目录即可
- 测试边界：
  - 插件内脚本始终可运行
  - 仓库根 `tests/` 仅在 source checkout 中存在
  - `full-tests` 在 standalone plugin 副本里返回 `unavailable` 属于设计边界

## 3. 六层模型速览

| 层 | 主要载体 | 职责 |
| --- | --- | --- |
| Layer 0 | Demand Intake（上游概念） | 需求进入系统前的最小 intake，不是运行态真相 |
| Layer 1 | `activities/<id>/1-contract.md` | 长期稳定约束、不可轻易漂移的规则 |
| Layer 2 | `activities/<id>/2-roadmap.md` | phase 级计划、依赖、退出条件 |
| Layer 3 | `activities/<id>/3-tasks/` | slice 级任务设计、验证、回滚、并行信息 |
| Layer 4 | `ACTIVE.md` | 唯一 live runtime truth，记录当前 focus 和活动卡片 |
| Layer 5 | `activities/<id>/4-decisions/` | 长期设计取舍和决策理由 |
| Layer 6 | `activities/<id>/5-memory/` / `local-state/` | 恢复辅助、closeout 产物、工作缓冲，不替代运行态真相 |

补充说明：

- `skills/`、`SKILL.md`、`AGENTS.md` 提供 prompt/protocol 规则入口。
- `scripts/` 是整个系统的执行面和校验面。
- `.codex-plugin/`、`agents/`、`assets/` 提供插件发现与交互元数据。
- `references/` 是辅助参考层，不是运行态真相。

## 4. 目录地图

| 路径 | 类型 | 说明 |
| --- | --- | --- |
| `ACTIVE.md` | 运行账本 | 当前 focus、活动索引、恢复指针 |
| `activities/` | 活动运行资产 | live activity 的 demand、contract、roadmap、tasks、decisions、memory |
| `recycle/` | 历史活动 | 已确认回收的 activity 目录与 `history.md` 索引 |
| `docs/` | 设计/验收文档 | spec、维护守则、acceptance、testing inventory 等 |
| `local-state/` | 本机状态 | closeout 与 telemetry，本地忽略，不作为分发真相 |
| `scripts/` | 核心代码 | 解析、校验、runner、closeout、wrapper、CLI |
| `references/` | 参考资料 | source map、checker 协议、安装/runtime 说明 |
| `.codex-plugin/` | 插件元数据 | `plugin.json` |
| `agents/` | 交互元数据 | agent interface 定义 |
| `assets/` | 视觉资源 | 插件 logo/icon |
| 仓库根 `tests/` | 开发测试 | repo-local 测试资产，不随插件单独分发 |

## 5. 推荐阅读顺序

1. `../../README.md`
2. `../../ACTIVE.md`
3. `../../skills/six-layer-execution-system/SKILL.md`
4. `architecture.md`
5. `modules-and-scripts.md`
6. `runtime-and-testing.md`

## 6. Code Wiki 导航

- `architecture.md`：整体架构、执行模型、数据流、依赖图
- `executive-flow-views.md`：适合汇报的简化总图，拆成总览图、需求分解图、执行交付图
- `complete-execution-flow.md`：完整执行流程图，包含需求分解子节点、checks、closeout、handoff
- `modules-and-scripts.md`：主要目录、脚本分类、关键类与函数说明
- `runtime-and-testing.md`：运行方式、命令入口、环境变量、验证与测试策略

## 7. 最小运行命令

在插件根目录执行：

```bash
python3 scripts/inspect_execution_system.py --format markdown
python3 scripts/run_execution_checks.py checks --timeout 60
python3 scripts/run_execution_checks.py full-tests --timeout 60
```

说明：

- `inspect` 输出当前插件和 ledger 快照。
- `checks` 会先跑插件内 hard-fail / advisory，再视 source checkout 是否存在决定是否追加 repo smoke tests。
- `full-tests` 会聚合 repo 根 `tests/` 与插件 acceptance/runner；没有仓库根 `tests/` 时会返回 `unavailable`。
