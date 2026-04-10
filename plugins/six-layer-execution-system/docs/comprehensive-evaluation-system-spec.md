# 六层执行系统全维评测系统规格说明书 (Comprehensive Evaluation System Specification)

## 1. 概述 (Overview)

### 1.1 背景与目标
为了衡量六层执行系统 (Six-Layer Execution System) 在复杂 AI 协作环境下的真实效能、架构纪律性以及生产就绪度，我们需要构建一套全维度的量化评测系统（Telemetry & Evaluation System）。
本规范基于《生产级优化与量化评估方案》及系统在契约、治理、上下文与安全层面的衍生需求，定义了评测系统的数据采集、处理、存储和指标计算标准。

### 1.2 核心设计原则
1. **零心智负担 (Zero Friction)**：数据采集（埋点）必须完全自动化，不依赖开发者或 Agent 的手动上报。
2. **多维交叉验证 (Cross-Validation)**：结合执行时间、静态文档状态和拦截日志，还原最真实的执行效能。
3. **低开销 (Low Overhead)**：遥测数据的收集和落盘不得阻塞执行系统的核心检查逻辑（耗时增加 < 10ms）。

---

## 2. 评测系统架构 (Architecture)

评测系统采用“旁路采集 - 异步聚合”架构，由以下四个核心组件构成：

1. **探针层 (Instrumentation Layer)**：
   - **CLI 拦截器 (CLI Interceptors)**：在 `exec` 工具链中自动注入耗时追踪和结果上报。
   - **检查器探针 (Checker Hooks)**：在 `run_execution_system_checks.py` 等脚本的生命周期钩子中注入状态检查。
   - **文档差异观测器 (Diff Observers)**：定期（如每次 Closeout）对比 Git HEAD 与 `ACTIVE.md` 的版本差异。
2. **本地落盘区 (Local Telemetry Sink)**：
   - 采用追加写入的本地 JSONL 格式 (`local-state/telemetry.jsonl`)，支持高频并发写入并确保数据不丢失。
3. **聚合分析引擎 (Aggregation Engine)**：
   - 独立的分析脚本 `scripts/analyze_telemetry.py`，负责从 JSONL 读取日志并计算 8 大维度的核心量化指标。
4. **报表层 (Reporting Layer)**：
   - 在每个迭代周期或大版本合并前，自动生成 Markdown 格式的评测报告（如 `docs/reports/eval_2026-Q2.md`）。

---

## 3. 全维量化指标字典 (Metrics Dictionary)

本系统将持续监控以下八大维度的核心指标（共 24 个细分指标，以下为核心清单）：

### 3.1 效率与可靠性基线 (Efficiency & Reliability)
| 指标名称 (Metric) | 采集来源 (Source) | 量化目标 (Target) | 计算逻辑 (Formula) |
| --- | --- | --- | --- |
| **恢复平均时间 (MTTR)** | Agent 启动日志与首个 CLI 耗时 | P95 < 5s | 从会话启动到首次发出有效状态流转指令的时长 |
| **切片交付周期 (Lead Time)** | `telemetry.jsonl` 中 Slice 状态机流转时间差 | 环比降 20% | `closed_out` 时间戳 - `planned` 时间戳 |
| **状态漂移发生率 (Drift Rate)** | `check_active_consistency.py` 报错拦截率 | 0次/迭代 | 漂移阻断次数 / 总检查次数 |
| **校验首通率 (First-Pass Yield)**| CLI 执行结果日志 | > 85% | 首次执行即 `Pass` 的提交次数 / 总提交次数 |

### 3.2 契约与规范遵从度 (Contracts & Specs Compliance)
| 指标名称 (Metric) | 采集来源 (Source) | 量化目标 (Target) | 计算逻辑 (Formula) |
| --- | --- | --- | --- |
| **单一真相违规率** | `check_execution_system_governance_consistency.py` | 0% | 非 `ACTIVE.md` 文档推演运行时状态的频率 |
| **闭环语义完整率** | `check_slice_closeout.py` | 100% | 成功闭环且包含 `validated` 字段的切片比例 |
| **契约边界越界率** | `telemetry.jsonl` (Contract Intercepts) | 趋近于0 | 尝试修改 Non-goals 模块的阻断拦截总数 |

### 3.3 治理与守卫有效性 (Governance & Guardrails)
| 指标名称 (Metric) | 采集来源 (Source) | 量化目标 (Target) | 计算逻辑 (Formula) |
| --- | --- | --- | --- |
| **无实质触发重开率** | `check_execution_system_maintenance_mode.py` | < 5% | Maintenance 模式下无 `Concrete Trigger` 的重启比例 |
| **治理语义偏离度** | 治理一致性检查脚本 | 0% | 各层文档关于维护协议的描述不一致告警数 |
| **建议规则噪音率** | CLI Warning 采集 | < 10% | 触发 Advisory 警告但未被采纳（或引发实际拆分）的比率 |

### 3.4 上下文与并发安全 (Context & Security)
| 指标名称 (Metric) | 采集来源 (Source) | 量化目标 (Target) | 计算逻辑 (Formula) |
| --- | --- | --- | --- |
| **缓冲膨胀重启率** | 工作缓冲观测器 | < 5% | `working-buffer.md` 被迫清空或进行状态压缩的频率 |
| **并发状态污染阻断率** | `check_parallel_safety.py` | - | 并发波次中发生 `shared_write_targets` 争抢的拦截数 |
| **非法焦点推进阻断率** | `check_active_wave_state.py` | 趋近于0 | 尝试推进 Non-focus 任务的阻断拦截总数 |

---

## 4. 遥测数据结构 (Telemetry Schema)

采集系统统一采用标准 JSON 格式进行落盘，确保后期解析的可扩展性。每一条数据称为一个 Event（事件）。

### 4.1 通用事件 Schema (Event Wrapper)
```json
{
  "timestamp": "2026-04-10T08:15:30Z",
  "event_type": "checker_execution | cli_action | state_transition | guardrail_block",
  "source": "check_parallel_safety.py",
  "execution_id": "exec-abc123xyz",
  "payload": {} 
}
```

### 4.2 拦截与告警负载 Schema (Guardrail Block Payload)
用于记录阻断率、噪音率及契约违规率。
```json
"payload": {
  "rule_id": "ERR_CONCURRENCY_POLLUTION",
  "severity": "hard_fail | advisory",
  "context": {
    "slice_id": "slice-401",
    "conflict_target": "src/utils.ts"
  },
  "resolution_action": "blocked"
}
```

---

## 5. 采集与埋点实现 (Instrumentation Implementation)

### 5.1 检查器侵入式埋点 (Checker Decorators)
在 Python 检查器中提供统一的 `@telemetry_trace` 装饰器：
```python
# scripts/telemetry.py (Proposed)
def telemetry_trace(event_type):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            log_event(event_type, duration, result)
            return result
        return wrapper
    return decorator
```

### 5.2 状态机钩子 (State Machine Hooks)
所有改变 `ACTIVE.md` 状态的 CLI 工具必须调用一次状态转移日志接口，明确记录 `From_State -> To_State`，从而准确计算切片交付周期（Lead Time）和并行效率。

---

## 6. 报告与治理闭环 (Reporting & Governance)

评测系统不仅是数据展示，更是改进执行系统本身规则的依据：
1. **周度降噪 (Weekly Denoising)**：如果“建议规则噪音率”连续两周 > 15%，说明某项规则阻力过大且无实效，应提报至 `Decisions` 层予以废除或降级。
2. **基线熔断 (Baseline Circuit Breaker)**：如果“首通率” < 70%，说明当前迭代对 Agent 的操作要求过于苛刻，强制暂停推行新的 Checker 规则，直到工具链自动化水平提升。
3. **性能衰退警报 (Regression Alerts)**：每次 PR 合并前，在 CI 环境运行模拟流转，若 Checker 平均耗时 > 1.5s，直接阻塞合入。