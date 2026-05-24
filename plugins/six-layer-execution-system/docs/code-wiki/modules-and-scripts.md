# 模块与脚本说明

## 1. 模块分组

### 1.1 规范与元数据模块

| 路径 | 作用 |
| --- | --- |
| `AGENTS.md` | subject root 约束与恢复顺序 |
| `skills/six-layer-execution-system/SKILL.md` | 唯一详细 prompt/protocol 规则源 |
| `.codex-plugin/plugin.json` | 插件元数据、展示文案、默认 prompt |
| `agents/openai.yaml` | agent interface 元信息 |

### 1.2 运行态与设计资产模块

| 路径 | 作用 |
| --- | --- |
| `ACTIVE.md` | 运行账本，唯一 live runtime truth |
| `activities/` | live activity 的 demand、contract、roadmap、tasks、decisions、memory |
| `recycle/` | 已确认回收的历史 activity 与 `history.md` |
| `docs/` | spec、acceptance、maintenance、testing inventory |
| `local-state/` | 本机 closeout artifact / telemetry，默认忽略 |
| `references/` | source map、checker 协议、安装/runtime 说明 |

### 1.3 执行代码模块

`scripts/` 是整个系统的核心代码区，可分为 8 组：

1. 路径与环境
2. ACTIVE 解析与操作
3. 结构/协议检查器
4. runner 与测试注册表
5. closeout / handoff
6. inspect / snapshot
7. CLI 与运维助手
8. telemetry

## 2. 核心 Python 文件总表

| 文件 | 角色 | 关键符号 | 主要依赖 |
| --- | --- | --- | --- |
| `execution_system_paths.py` | 路径/环境底座 | `WORKSPACE`、`resolve_workspace_path()` | `os`、`pathlib` |
| `plugin_paths.py` | wrapper 环境桥接 | `build_env()`、`run_root_script()` | `execution_system_paths` |
| `active_ledger.py` | ACTIVE parser/model | `Activity`、`Ledger`、`parse_ledger()` | `execution_system_paths` |
| `check_active_consistency.py` | ACTIVE hard-fail checker | `validate_*()` | `active_ledger`、`git` |
| `check_demand_card_schema.py` | demand schema checker | `main()` | `demand_card` |
| `check_task_slice_schema.py` | tasks schema checker | `validate_task_doc()` | `execution_system_paths` |
| `check_task_dependency_graph.py` | DAG checker | `parse_dep_values()`、`validate_task_doc()` | `execution_system_paths` |
| `check_parallel_safety.py` | 并行安全 checker | `parse_list_field()`、`validate_task_doc()` | `execution_system_paths` |
| `check_active_wave_state.py` | ACTIVE 波次状态 checker | `has_any_wave_state()`、`validate_task_doc()` | `active_ledger` |
| `check_execution_system_governance_consistency.py` | 协议一致性 checker | `expect_contains()` | `execution_system_paths` |
| `check_execution_system_status_freshness.py` | 文档状态新鲜度 checker | `find_problems()` | `execution_system_paths` |
| `check_oversized_migration_slices.py` | advisory checker | `advisory_reasons()` | `execution_system_paths` |
| `execution_system_suite.py` | runner 注册表 | `CHECK_SCRIPT_NAMES`、`FULL_REPO_TEST_SPECS` | `execution_system_paths` |
| `run_execution_system_checks.py` | 统一 checks runner | `ExecutionSystemSummary`、`collect_summary()` | `execution_system_suite`、`telemetry` |
| `run_execution_system_full_tests.py` | 统一 full suite runner | `main()` | `execution_system_suite`、`run_execution_system_checks` |
| `accept_active_ledger_v2.py` | ACTIVE 验收入口 | `run_check()` | `collect_summary()` |
| `check_closeout_ready.py` | closeout 准入门禁 | `main()` | `collect_summary()`、`parse_ledger()` |
| `create_slice_closeout.py` | closeout artifact writer | `create_closeout()` | `execution_system_paths` |
| `check_slice_closeout.py` | closeout artifact verifier | `main()` | `execution_system_paths` |
| `build_slice_handoff.py` | handoff payload builder | `build_handoff_payload()` | `execution_system_paths` |
| `complete_slice.py` | closeout orchestration | `prepare_slice()`、`payload_slice()` | closeout 相关模块 |
| `execution_system_snapshot.py` | 系统快照生成 | `build_snapshot()`、`to_markdown()` | `active_ledger.py` 动态导入 |
| `inspect_execution_system.py` | inspect 包装入口 | `main()` | `execution_system_snapshot` |
| `run_local_execution_checks.py` | 本地 runner wrapper | `COMMANDS`、`main()` | `execution_system_suite` |
| `run_execution_checks.py` | 插件公开 wrapper | `run_root_script()` | `plugin_paths` |
| `exec_sys.py` | 统一 CLI | `slice start`、`slice complete`、`status` | `active_ledger`、`complete_slice` |
| `decomposition_engine.py` | 自动分解引擎 | `decompose_request()` | `active_ledger`、`demand_card` |
| `demand_card.py` | demand 模型与 schema | `DemandCard`、`render_demand_card()` | 标准库 |
| `set_focus_activity.py` | focus 切换工具 | `main()` | `ACTIVE.md` 文本替换 |
| `validate_focus_first.py` | focus-first 验证器 | `main()` | `active_ledger` |
| `telemetry.py` | 观测记录 | `record_event_safely()`、`with_telemetry()` | `execution_system_paths` |

## 3. 关键类与函数

### 3.1 `active_ledger.py`

### `Activity`

作用：

- 表示 `ACTIVE.md` 中的单个 activity card
- 提供对 scalar/list 字段的访问
- 支持基于原始文本块的就地更新与保存

关键成员：

- `activity_id` / `type` / `status`
- `current_slice_id` / `next_slice_id` / `last_commit`
- `scalar(key)`：读取标量字段
- `items(key)`：读取列表字段
- `update_fields(**updates)`：更新字段并同步回原始文本
- `save()`：委托给所属 `Ledger` 落盘

### `Ledger`

作用：

- 表示整个 `ACTIVE.md`
- 管理 ledger meta、activity index 与活动卡片集合
- 提供 focus activity、runnable activities、整体保存能力

关键方法：

- `get_current_focus_activity()`
- `list_activities()`
- `list_runnable_activities()`
- `update_fields(**updates)`
- `save()`

### `parse_ledger(path=ACTIVE)`

作用：

- 读取 `ACTIVE.md`
- 解析 `Ledger meta`、`Activity index`、`Activities`
- 将 Markdown 文本转换为 `Ledger + Activity`

这是整个系统最核心的数据入口之一，许多 checker、runner、closeout 脚本都基于它工作。

### 3.2 `run_execution_system_checks.py`

### `ExecutionSystemSummary`

统一 summary 数据结构，包含：

- `hard_fail_status`
- `first_failing_command`
- `advisory_commands`
- repo smoke tests 的状态、数量、根路径、原因

### `discover_repo_tests_root()`

作用：

- 判断当前是否处于 source checkout 场景
- 自动发现仓库根 `tests/`
- 用于区分：
  - standalone plugin
  - source checkout without tests
  - source checkout with tests

### `collect_summary(print_output=True)`

作用：

- 先执行 hard-fail checkers
- 再执行 advisory checks
- 最后在可用时执行 repo smoke tests
- 输出或返回统一 summary

这是整个校验体系的总入口。

### `summary_footer(summary)`

作用：

- 把 summary 规范化为稳定的文本 footer
- 提供 `hard_fail_status`、`first_failing_command`、`recovery_hint`
- 也是多条 path 测试的稳定断言面

### 3.3 closeout / handoff 链路

### `check_closeout_ready.py::main()`

职责：

- 复用 `collect_summary()`，确认 hard-fail suite 通过
- 校验当前 focus activity 必须是 roadmap
- 校验 `current_slice_id / next_slice_id / last_commit / last_validation` 不能为空

### `create_slice_closeout.py::create_closeout()`

职责：

- 生成 `local-state/last-slice-closeout.json`
- 写入切片完成产物

关键字段：

- `dedupe_key`
- `activity_id`
- `current_focus_activity_id`
- `completed_slice_id`
- `next_slice_id`
- `validation_state`
- `slice_state`
- `commit`
- `validations`

### `check_slice_closeout.py::main()`

职责：

- 校验 closeout artifact 是否存在
- 校验 `validation_state=validated`
- 校验 `slice_state=closed_out`
- 对 roadmap activity 校验 `current_focus_activity_id == activity_id`

### `build_slice_handoff.py::build_handoff_payload()`

职责：

- 从 frozen closeout artifact 构建 handoff payload
- 明确避免重新依赖 live `ACTIVE.md`

### `complete_slice.py::prepare_slice()`

职责：

- 串起 checks -> ready gate -> create_closeout -> build_handoff_payload
- 是 canonical closeout entrypoint

### 3.4 checker 族

### `check_active_consistency.py`

职责：

- 校验 `ACTIVE.md` 的 ledger meta、活动索引、focus activity、字段约束
- 校验 focus activity 文档路径是否存在
- 校验 `last_commit` 在 git repo 中可解析
- 检测 ACTIVE-only 自漂移

关键函数：

- `validate_ledger_level()`
- `validate_common_activity_fields()`
- `validate_roadmap_activity()`
- `validate_waiting_activity()`
- `validate_simple_activity()`
- `validate_focus_level()`

### `check_demand_card_schema.py`

职责：

- 扫描 `activities/*/0-demand.md` 或指定 demand 文件
- 校验 demand intake 是否具备最小 schema
- 保护“自然语言需求上游工件”不会退化成无结构文本

### `check_task_slice_schema.py`

职责：

- 校验 migrated task doc 的 slice 是否具备 `phase_id` 与 `rollback_strategy`

### `check_task_dependency_graph.py`

职责：

- 解析 `depends_on`
- 校验引用合法、是否依赖自身、是否引用未知 slice
- 检测 dependency cycle

### `check_parallel_safety.py`

职责：

- 校验 `parallel_safe` 与 `shared_write_targets` 是否一致
- 约束“可并行”声明必须与写面说明匹配

### `check_active_wave_state.py`

职责：

- 检查 wave-state 字段是否只出现在 roadmap activity
- 校验 `execution_mode`、`current_wave_id`、`integration_step`
- 防止把 serial activity 错写成波次状态

### 3.5 工具与观测

### `execution_system_snapshot.py`

作用：

- 汇总 docs、skills、ledger 快照
- 支持 JSON / Markdown 输出
- 被 `inspect_execution_system.py` 复用

### `exec_sys.py`

统一 CLI，包括：

- `slice start <id>`：更新 focus activity 的 `current_slice_id`
- `slice complete [--agile]`：跑 checks 并执行 closeout
- `status`：打印当前 focus activity 概况
- `demand decompose --request ... [--activate]`：把自然语言需求生成 demand/roadmap/tasks/ACTIVE 草案

### `decomposition_engine.py`

作用：

- 将自然语言需求做确定性分解
- 生成 `activities/<activity-id>/` 和 `ACTIVE` activity
- 当前是一阶段规则引擎，不依赖外部模型

### `telemetry.py`

提供：

- `record_event()`：写入 JSONL telemetry
- `record_event_safely()`：失败静默降级
- `with_telemetry()`：装饰器形式的埋点

当前 `run_execution_system_checks.py` 已通过装饰器接入 telemetry。

## 4. 测试模块说明

仓库根 `tests/` 采用“smoke + path + clone workspace”混合策略。

| 测试类型 | 代表文件 | 说明 |
| --- | --- | --- |
| checker smoke | `test_check_active_consistency.py` 等 | 验证单个 checker 的规则 |
| path test | `test_execution_system_path_chain.py` 等 | 验证多脚本串联后的协议不漂移 |
| runner smoke | `test_run_execution_system_checks.py` | 验证统一 runner、summary footer、telemetry |
| suite registry | `test_execution_system_suite_registry.py` | 验证注册表与实际命令集合不漂移 |
| clone workspace | `test_workspace_clone.py` | 在临时副本里模拟 standalone/source checkout 场景 |

其中 `test_workspace_clone.py` 很关键，因为它把测试从“当前工作副本”隔离为“可复制插件”的真实运行模型。
