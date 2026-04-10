# 运行方式与测试体系

## 1. 运行前提

### 1.1 必需条件

- 已安装 `python3`
- 已安装 `git`
- 当前目录为插件根，或使用 wrapper 时能正确定位插件根

### 1.2 依赖特征

- 运行时只使用 Python 标准库
- 未发现第三方 Python 依赖清单
- 需要 `git` 支持以下能力：
  - 解析 `HEAD`
  - 验证 `last_commit`
  - 检查工作区改动
  - 初始化临时测试仓库

## 2. 目录与路径约定

### 2.1 subject root

真正的运行根是：

`plugins/six-layer-execution-system/`

不是仓库根。

### 2.2 核心路径变量

`scripts/execution_system_paths.py` 定义了路径解析基座：

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `PLUGIN_ROOT` | 当前脚本上级目录 | 插件物理根目录 |
| `REPO_ROOT` | `SIX_LAYER_REPO_ROOT` 或 `PLUGIN_ROOT` | 逻辑 repo 根 |
| `WORKSPACE` | `SIX_LAYER_WORKSPACE` 或 `REPO_ROOT` | 运行工作根 |
| `STATE_ROOT` | `SIX_LAYER_STATE_ROOT` 或 `REPO_ROOT/local-state` | 本地状态目录 |

### 2.3 环境变量

| 环境变量 | 作用 |
| --- | --- |
| `SIX_LAYER_REPO_ROOT` | 覆盖逻辑 repo 根 |
| `SIX_LAYER_WORKSPACE` | 覆盖运行工作根 |
| `SIX_LAYER_STATE_ROOT` | 覆盖 telemetry/state 输出目录 |
| `SIX_LAYER_SOURCE_REPO_ROOT` | 指定 source checkout 根，供 runner 发现 `tests/` |
| `SIX_LAYER_EXECUTION_MODE=agile` | 让 `slice complete --agile` 跳过 repo smoke tests |
| `TELEMETRY_FILE_PATH` | 覆盖 telemetry JSONL 输出文件 |
| `TELEMETRY_DEBUG` | telemetry 写入失败时打印调试信息 |

## 3. 公开命令入口

### 3.1 inspect

```bash
python3 scripts/inspect_execution_system.py --format markdown
```

作用：

- 打印插件快照
- 列出 docs / skills
- 打印 ledger 摘要与当前 focus activity

等价内核：

- `scripts/execution_system_snapshot.py`

### 3.2 checks

```bash
python3 scripts/run_execution_checks.py checks --timeout 60
```

对外公开 wrapper：

- `scripts/run_execution_checks.py`

真实执行入口：

- `scripts/run_local_execution_checks.py checks --timeout 60`
- `scripts/run_execution_system_checks.py`

执行顺序：

1. hard-fail checkers
2. advisory checkers
3. repo smoke tests（如果可用）
4. 输出统一 summary footer
5. 写 telemetry

### 3.3 active / closeout-ready

```bash
python3 scripts/run_execution_checks.py active --timeout 60
python3 scripts/run_execution_checks.py closeout-ready --timeout 60
```

说明：

- `active` 只校验 ACTIVE 一致性
- `closeout-ready` 验证是否具备执行 closeout 的最低条件

### 3.4 full-tests

```bash
python3 scripts/run_execution_checks.py full-tests --timeout 60
```

行为特点：

- 需要 source checkout 根存在 `tests/`
- 聚合 repo 根 path/smoke tests 与插件 acceptance/runner
- standalone plugin 会返回 `EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE`

### 3.5 统一 CLI

```bash
python3 scripts/exec_sys.py status
python3 scripts/exec_sys.py slice start <slice_id>
python3 scripts/exec_sys.py slice complete
python3 scripts/exec_sys.py slice complete --agile
python3 scripts/exec_sys.py demand decompose --title "..." --request "..."
python3 scripts/exec_sys.py demand decompose --request-file /abs/path/request.txt --activate
```

说明：

- `status`：查看当前 focus activity
- `slice start`：修改 focus activity 的 `current_slice_id`
- `slice complete`：执行 checks + closeout + payload 输出
- `--agile`：跳过 repo smoke tests，适合快速 closeout
- `demand decompose`：把自然语言需求生成 `demands/*.md`、`roadmaps/*-roadmap.md`、`tasks/*-tasks.md` 和 `ACTIVE` activity

## 4. 检查器与 runner 体系

### 4.1 hard-fail checkers

由 `execution_system_suite.py::CHECK_SCRIPT_NAMES` 注册：

- `check_active_consistency.py`
- `check_demand_card_schema.py`
- `check_task_slice_schema.py`
- `check_task_dependency_graph.py`
- `check_parallel_safety.py`
- `check_active_wave_state.py`
- `check_execution_system_governance_consistency.py`
- `check_execution_system_status_freshness.py`

只要其中一个失败，`run_execution_system_checks.py` 立即失败，并记录第一条失败命令。

### 4.2 advisory checkers

当前注册：

- `check_oversized_migration_slices.py`

特点：

- 告警但不 hard-fail
- 出现在 summary footer 的 `advisory_command`

### 4.3 repo smoke tests

由 `execution_system_suite.py::REPO_SMOKE_TESTS` 注册，典型包括：

- ACTIVE checker smoke
- task schema smoke
- dependency graph smoke
- parallel safety smoke
- active wave-state smoke
- governance consistency smoke
- status freshness smoke

作用：

- 用 source checkout 根 `tests/` 做最小回归
- 保证脚本规则与 repo-local 测试面一致

### 4.4 full suite

`run_execution_system_full_tests.py` 会聚合：

- repo 根 path tests
- smoke tests
- closeout tests
- acceptance
- runner 自检

它是协议/runner 类变更后的推荐验证入口。

## 5. closeout 与 handoff

### 5.1 closeout-ready 门禁

closeout 前至少满足：

- hard-fail suite 通过
- 当前 focus activity 存在
- focus activity 类型为 `roadmap`
- `current_slice_id` 不为空
- `next_slice_id` 不为空
- `last_commit` 不为空
- `last_validation` 不为空

### 5.2 closeout artifact

路径：

- `memory/last-slice-closeout.json`

主要字段：

- `dedupe_key`
- `activity_id`
- `current_focus_activity_id`
- `activity_type`
- `repo`
- `completed_slice_id`
- `next_slice_id`
- `validation_state`
- `slice_state`
- `commit`
- `validations`
- `message`
- `created_at`

### 5.3 handoff payload

由 `build_slice_handoff.py` 从 closeout artifact 生成，避免重新回读 live `ACTIVE.md` 造成身份漂移。

## 6. telemetry 与本地状态

默认 telemetry 文件：

- `local-state/telemetry.jsonl`

特征：

- JSON Lines 格式
- 记录事件时间、事件类型、payload
- `run_execution_system_checks.py` 默认接入

当前典型事件：

- `execution_system_check`

payload 里会记录：

- `status`
- `first_failing_command`
- `hard_fail_status`
- `repo_smoke_tests_status`
- `elapsed_seconds`

## 7. 测试策略

### 7.1 测试哲学

这个项目的测试不是围绕业务功能，而是围绕 **执行协议不漂移** 展开：

- checker smoke：验证单条规则
- path tests：验证多脚本串联协议
- clone workspace tests：验证插件可复制运行
- registry tests：验证命令注册表不漂移

### 7.2 代表性测试

| 文件 | 关注点 |
| --- | --- |
| `tests/test_execution_system_path_chain.py` | checks -> closeout-ready -> acceptance 的快乐路径 |
| `tests/test_run_execution_system_checks.py` | summary footer、telemetry、repo smoke status 分支 |
| `tests/test_execution_system_path_parallel_wave.py` | parallel-wave 相关协议 |
| `tests/test_execution_system_path_closeout_payload_identity.py` | closeout artifact 到 handoff payload 的字段传递 |
| `tests/test_execution_system_suite_registry.py` | suite registry 不漂移 |
| `tests/test_workspace_clone.py` | 临时复制工作区与 Git 初始化辅助 |

### 7.3 何时跑什么

| 改动类型 | 推荐命令 |
| --- | --- |
| 文档或单一字段类小改 | `python3 scripts/run_execution_checks.py checks --timeout 60` |
| checker 规则变更 | `checks` + 最近的 smoke test |
| payload / closeout 协议变更 | `full-tests` |
| runner 组合或 summary 变更 | `full-tests` |
| 只想确认当前账本是否健康 | `python3 scripts/run_execution_checks.py active --timeout 60` |

## 8. 运行边界与常见误区

- 不要把仓库根当成 execution-system 的 runtime truth。
- 不要从 `memory/` 或聊天历史推断当前状态，应先读 `ACTIVE.md`。
- 不要把 standalone plugin 中 `full-tests unavailable` 误判成系统故障。
- 不要把 advisory 输出当成 hard-fail。
- closeout/handoff 的最终事实在 `memory/last-slice-closeout.json`，不是 live `ACTIVE.md`。
