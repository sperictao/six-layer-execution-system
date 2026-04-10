# 六层执行系统：生产级优化与量化评估方案

## 1. 背景与目标
当前的六层执行系统（Six-Layer Execution System）虽然在“防漂移”和“上下文无损恢复”上表现优异，但其极高的维护心智负担、僵化的状态机以及散落的脚本工具链限制了其在生产环境的大规模推广。
本方案旨在通过**自动化降本**、**柔性状态机**和**统一工具链**等手段对系统进行生产级优化，并提供一套**完整且可量化的评估指标体系**，以衡量系统优化的 ROI（投资回报率）与生产就绪度。

---

## 2. 生产级优化方案 (Production Optimization)

### 2.1 统一的自动化 CLI 工具链 (Unified CLI Tooling)
目前状态流转高度依赖人工修改 `ACTIVE.md` 和 `tasks.md`，极易遗漏字段。
**优化动作**：
- **封装 `exec` 命令行工具**：将散落的 Python 和 Shell 脚本整合为统一命令。例如：
  - `exec slice start <slice_id>`: 自动更新 ACTIVE 层的焦点状态。
  - `exec slice complete`: 自动运行检查、生成 Closeout 工件并更新状态机。
  - `exec status`: 可视化展示当前焦点活动和阻塞依赖。

### 2.2 柔性分级状态机 (Adaptive State Machine)
当前的 Hard-fail 规则对所有任务一视同仁（例如强制要求 `rollback_strategy`），影响开发心流。
**优化动作**：
- **引入执行模式 (Execution Modes)**：
  - `Agile Mode`：适用于 `simple` 或 `refactor` 类型的短期任务，放宽部分强制校验（如回滚策略），侧重快速闭环。
  - `Strict Mode`：适用于 `roadmap` 级别的高风险任务，严格执行六层强制收官协议（Closeout Pipeline）。

### 2.3 状态自动同步与依赖图 (Automated Sync & DAG)
**优化动作**：
- 增强 `Tasks Layer` 到 `ACTIVE Layer` 的单向流转自动化。当通过工具链标记某个 Task `validated` 时，系统自动完成 `ACTIVE.md` 中 `ready_slices` 和 `inflight_slices` 的状态推演，并推进下一个并发波次（Parallel-Wave）。

### 2.4 可观测性与遥测打点 (Observability & Telemetry)
**优化动作**：
- 在所有的 Checker 和 CLI 工具中埋点，记录状态流转的耗时、Checker 的报错原因以及拦截率。这些数据将直接支撑后续的量化评估。

---

## 3. 可量化的核心评估指标体系 (Quantifiable Metrics)

为了验证系统在生产环境的有效性，我们将评估体系拆分为四个核心维度（A-D）：

### 维度 A：可靠性与防漂移 (Reliability & Anti-Drift)
衡量系统对抗 AI 上下文遗忘和多源真相冲突的核心能力。
1. **MTTR (Mean Time To Recovery - 恢复平均时间)**
   - **定义**：会话中断或清空后，系统读取 `ACTIVE.md` 并完全恢复上下文（定位焦点、找到阻点）所需的平均时间。
   - **量化目标**：**P95 < 5 秒**。
2. **Drift Incident Rate (状态漂移发生率)**
   - **定义**：系统自动巡检时，发现 `ACTIVE.md` 的 `last_commit` 与代码库真实 `HEAD` 不一致的频次。
   - **量化目标**：**0 次 / 迭代周期**（或 < 1% 的状态流转）。

### 维度 B：系统开销与阻力 (Overhead & Friction)
衡量规范执行带来的额外成本，直接关系到开发者的抵触情绪。
1. **Administrative Overhead Ratio (管理开销比)**
   - **定义**：(维护各层文档状态 + 运行校验脚本的时间) / (完成该切片的总耗时) * 100%。
   - **量化目标**：**< 10%**。如果一个任务写代码 50 分钟，文档更新不应超过 5 分钟。
2. **Checker First-Pass Yield (校验首通率)**
   - **定义**：开发者或 Agent 提交状态变更时，自动化检查脚本（如 `run_execution_system_checks.py`）首次即通过的比例。
   - **量化目标**：**> 85%**。首通率过低说明系统字段要求过于繁琐或错误提示不清晰。

### 维度 C：执行吞吐量与并行效率 (Throughput & Concurrency)
衡量六层系统引入“并行波次 (Parallel-Wave)”调度后的实际加速效果。
1. **Slice Lead Time (切片交付周期)**
   - **定义**：一个 Slice 从 `planned` 流转到 `closed_out` 的端到端平均耗时。
   - **量化目标**：环比（未使用该系统前）下降 **20%**。
2. **Parallel Execution Ratio (并发执行比率)**
   - **定义**：同一焦点活动下，处于并发波次（无共享写目标的 Independent Slices）中的切片数量 / 总切片数量。
   - **量化目标**：对于复杂任务，目标达到 **> 30%** 的并发覆盖率。

### 维度 D：工具链性能 (Tooling Performance)
1. **Checker Execution Time (校验执行耗时)**
   - **定义**：统一校验脚本运行的端到端耗时。
   - **量化目标**：**P95 < 1.5 秒**（必须是毫秒级反馈，否则严重打断心流）。
2. **False Positive Rate (校验误报率)**
   - **定义**：Checker 抛出错误或警告，但实际状态和文档逻辑是正确的比率（例如将合规的合并动作误判为 Oversized slice）。
   - **量化目标**：**< 2%**。

---

## 4. 评估实施路径 (Evaluation Implementation Plan)

1. **Phase 1: 埋点与基线收集 (Baseline Collection)**
   - 改造当前的 `scripts/run_execution_system_checks.py`，将每次运行的耗时、结果（Pass/Fail/Warn）和失败规则输出到本地 `.trae/telemetry.jsonl` 中。
   - 在不改变当前流程的情况下运行 1-2 个 Roadmap 任务，收集**管理开销比**和**校验首通率**基线。
2. **Phase 2: 自动化 CLI 灰度上线 (CLI Canary Release)**
   - 推出封装好的 `exec` 工具链，替换手动修改 `ACTIVE.md` 的操作。
   - 对比新老方式下的 **管理开销比 (Overhead Ratio)**，验证自动化降本效果。
3. **Phase 3: 全面指标验收 (Full Assessment)**
   - 根据收集到的遥测数据，出具《六层执行系统生产效能报告》。若满足所有量化目标（如 Overhead < 10%, MTTR < 5s），则正式认定该系统达到**生产就绪 (Production-Ready)** 状态。
