# 需求分解器真实需求演练测试报告

## 1. 目标

对当前仓库中的需求分解器执行一次接近真实使用方式的完整验证，回答三个问题：

1. 现有完整测试套件是否全绿。
2. 自然语言需求是否能在隔离工作区中稳定生成 `demand/roadmap/tasks/ACTIVE` 四类工件。
3. 生成结果在可执行性、可恢复性和可观测性上是否达到当前设计预期。

测试时间：`2026-04-10`

主体目录：`plugins/six-layer-execution-system/`

---

## 2. 测试范围与方法

### 2.1 基线校验

在仓库根目录执行：

```bash
python3 "plugins/six-layer-execution-system/scripts/run_execution_checks.py" checks --timeout 60
PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts" \
python3 "plugins/six-layer-execution-system/scripts/run_execution_system_full_tests.py"
```

目的：

- 验证当前插件目录与 repo-root `tests/` 的集成链路。
- 验证 unified runner、full suite、acceptance 和 path smoke 之间没有断链。

### 2.2 真实需求隔离演练

为了避免污染 live ledger，在临时工作区复制 `plugins/six-layer-execution-system/` 后执行手工演练。

演练输入：

```text
新增一条真实需求演练链路：给需求分解器一段自然语言需求后，自动生成 demand/roadmap/tasks，并在最后补一份可交付的测试报告草稿。只允许改生成链路相关脚本和文档，不要重写现有 closeout 协议，不要改动 ACTIVE 里已有活动，先保持串行分解，人工 review 通过后再决定是否激活。
```

执行命令：

```bash
SIX_LAYER_REPO_ROOT="/tmp/.../workspace" \
SIX_LAYER_WORKSPACE="/tmp/.../workspace" \
python3 "/tmp/.../workspace/scripts/exec_sys.py" demand decompose \
  --title "真实需求演练报告链路" \
  --request "<上面的自然语言需求>"
```

随后补跑：

```bash
python3 scripts/check_demand_card_schema.py <generated-demand>
python3 scripts/check_generated_decomposition_consistency.py
python3 scripts/run_execution_system_checks.py
```

---

## 3. 结果摘要

### 3.1 仓库基线

- `run_execution_checks.py checks --timeout 60`：通过
- `run_execution_system_full_tests.py`：通过
- full suite 总数：`29`
- full suite 失败数：`0`

说明：

- `system-path-hard-fail` 用例内部会故意触发一段 `ACTIVE_LEDGER_V2_ACCEPTANCE_FAILED` 负向输出，用于验证 hard-fail 路径本身；这不是整套 full suite 失败。
- unified runner 最终摘要为 `EXECUTION_SYSTEM_CHECKS_OK`，repo smoke tests 为 `passed`。

### 3.2 真实需求演练

需求分解命令返回：

- `title`: `真实需求演练报告链路`
- `task_type`: `testing`
- `risk_level`: `medium`
- `strategy`: `testing-delivery`
- `activity_id`: `auto-request-5117a99a`
- `demand_doc`: `demands/2026-04-10-request-5117a99a.md`
- `roadmap_doc`: `roadmaps/request-5117a99a-roadmap.md`
- `tasks_doc`: `tasks/request-5117a99a-tasks.md`
- `current_slice_id`: `5R-A.A1`
- `next_slice_id`: `5R-A.B1`
- `status`: `ready`
- `autopilot`: `true`
- `activated`: `false`

演练后的校验结果：

- `check_demand_card_schema.py`：通过
- `check_generated_decomposition_consistency.py`：通过，`scanned_activities: 2`
- 临时工作区 `run_execution_system_checks.py`：通过
- 临时工作区 telemetry 已写入 `local-state/telemetry.jsonl`

临时工作区 runner 遥测样本：

- `status`: `passed`
- `hard_fail_status`: `passed`
- `repo_smoke_tests_status`: `skipped`
- `elapsed_seconds`: `0.30928730964660645`

---

## 4. 生成物抽样评估

### 4.1 正向表现

1. 分类结果基本合理
   - 这条输入同时包含“测试报告”“约束”“不要改动已有活动”等信号，系统最终归类为 `testing`、风险为 `medium`，与输入语义基本一致。

2. 计划结构完整
   - 自动生成了 `demand/roadmap/tasks/ACTIVE` 四类工件。
   - roadmap 拆成 `Demand normalization -> Test backlog planning -> Validation and handoff` 三阶段，符合 testing-delivery 的预期。
   - tasks 文档形成串行依赖链 `A1 -> B1 -> C1`，并为每个 slice 给出 `validation`、`rollback_strategy`、`handoff_output`。

3. 激活边界控制正确
   - 新活动被写入 `ACTIVE.md`，但没有抢占 `current_focus_activity_id`。
   - live focus 仍然保持 `waiting-ledger-review`，说明“生成 backlog”和“切换焦点”已经分离。

4. 可观测性链路可用
   - 临时工作区 runner 自动写 telemetry。
   - 基线仓库 runner 和临时工作区 runner 都能给出统一 summary footer。

### 4.2 设计观察与改进建议

1. 中文标题的 slug 可读性弱
   - 本次标题为中文，最终生成路径退化为 `request-5117a99a`。
   - 这保证了稳定性，但会显著降低人工检索、review 和文档可读性。
   - 建议：为非 ASCII 标题增加拼音/可配置别名/显式 `--slug` 入口，而不是直接回落到 hash。

2. `constraints` 与 `non_goals` 抽取会出现重复
   - 本次输入中的同一整句同时命中了 `只` 和 `不要` 规则，结果同一句被同时写入 `constraints` 与 `non_goals`。
   - 这不影响 checker，但会降低需求卡的表达质量。
   - 建议：把“限制条件”和“明确不做”拆成两套更窄的抽取规则，或在生成后做去重与重分类。

3. generated backlog 没有被 runner 做逐文档结构校验
   - 临时工作区 runner 通过了，但它调用的 `check_task_slice_schema.py`、`check_task_dependency_graph.py`、`check_parallel_safety.py` 默认仍检查 canonical task docs，而不是新生成的 `tasks/request-5117a99a-tasks.md`。
   - 当前 generated backlog 的结构正确性，更多依赖生成器本身和 `check_generated_decomposition_consistency.py` 的跨工件一致性检查。
   - 这意味着“生成物已存在，但新任务文档结构本身略有漂移”的问题，不一定会在统一 runner 中第一时间暴露。
   - 建议：让 generated activity 注册其 `tasks_doc` 后，被 runner 自动纳入 schema / DAG / parallel-safety 的逐文档检查。

4. `advisory_hits` 命名与语义存在偏差
   - 当前 runner 只要 advisory 脚本成功执行，就会把它计入 `advisory_hits`。
   - 因此即使输出是 `OVERSIZED_MIGRATION_SLICE_OK`，summary 仍显示 `advisory_hits: 1`。
   - 这更接近“advisory pipeline executed”而不是“发现 1 个告警”。
   - 建议：把统计拆成 `advisory_commands_run` 和 `advisory_warning_count`，避免误读。

---

## 5. 结论

结论分两层：

1. 作为仓库实现状态
   - 当前需求分解器已经具备可运行、可校验、可恢复的主链路。
   - 完整测试套件 `29/29` 通过，`demand decompose` 路径和 full runner 集成都已打通。

2. 作为“真实需求入口”的产品化程度
   - 已经达到“可以演示、可以落地试跑”的水平。
   - 但要说“生产级好用”，还差几刀明确的体验与治理补强：
     - 非 ASCII slug 可读性
     - constraints / non_goals 去重与重分类
     - generated tasks 纳入 unified runner 的逐文档结构校验
     - advisory 指标语义纠偏

综合判断：

- 当前版本可以作为需求分解器 v1 使用。
- 如果要把它当成“面向真实团队日常 intake 的稳定入口”，优先级最高的补强项是第 3 点，也就是把生成物本身纳入统一 runner 的真实结构校验闭环。
