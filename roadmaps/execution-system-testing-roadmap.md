# execution system testing roadmap

## Goal
- 为 `execution-system-spec-v1` 建立完整测试体系，覆盖结构、语义、execution-system path、maintenance mode 与治理语义。
- 让执行系统的可靠性不只依赖若干零散 smoke，而是具备可解释、可扩展、可持续维护的测试矩阵。

## Contract reference
- `docs/execution-system-spec-v1.md`
- `docs/execution-system-spec-v1-acceptance-checklist.md`
- `docs/execution-system-maintenance-guardrails.md`

## Validation baseline
- `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/accept_active_ledger_v2.py`
- `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_checks.py`
- 现有 smoke 全绿
- 不破坏 business focus 的默认推进

## Phases

### Phase 1 - Test foundation inventory
- objective:
  - 盘点现有 execution-system 测试资产，并建立统一测试分层模型
- dependencies:
  - 当前 execution-system checker / advisory / acceptance / closeout 已可运行
- outputs:
  - 测试分层图（layout / semantics / smoke / execution-system path / governance）
  - 已有测试与缺口列表
- exit criteria:
  - 明确哪些测试已经存在
  - 明确缺的关键链路与治理测试
- risks:
  - 只做文档盘点，不真正转化为可执行 backlog

### Phase 2 - Semantic coverage strengthening
- objective:
  - 把当前 execution-system 的关键语义进一步收口成可重复运行的单测与 smoke
- dependencies:
  - Phase 1
- outputs:
  - 更稳定的语义测试簇
  - 统一命名与职责清晰的 smoke/semantic 测试集合
- exit criteria:
  - 当前 checker / advisory / closeout / summary 的语义测试边界清楚
- risks:
  - 过早追求全面覆盖而引入脆弱测试

### Phase 3 - Execution-system path matrix coverage
- objective:
  - 建立 execution system 的关键路径矩阵测试
- dependencies:
  - Phase 2
- outputs:
  - hard-fail path
  - advisory-only path
  - policy-gate path
  - closeout-blocked path
  - focus-switch path
- exit criteria:
  - 关键 execution-system path 组合都有链路测试
- risks:
  - 依赖真实 workspace 状态过多，导致测试过脆

### Phase 4 - Governance and maintenance-mode checks
- objective:
  - 为 maintenance mode / reopen conditions / re-entry protocol 增加轻量治理检查
- dependencies:
  - Phase 3
- outputs:
  - maintenance-mode consistency checks
  - reopen / re-entry consistency checks
- exit criteria:
  - 治理语义不再只靠人工记忆
- risks:
  - 把治理语义过度硬编码，造成形式主义

### Phase 5 - Unified test entrypoint and acceptance report
- objective:
  - 将 execution-system 的完整测试矩阵汇总为统一入口和可读报告
- dependencies:
  - Phases 1-4
- outputs:
  - 统一测试入口
  - 文档化测试回执模板
- exit criteria:
  - 能一键运行 execution-system 全量测试集
  - 输出清楚区分 fail / advisory / policy-gate / governance review
- risks:
  - 把测试入口做成新的复杂平台，而不是薄封装

## Current recommended phase
- Phase 5 - Unified full-test entrypoint (`ET-E.E1` remains the current recommended phase; the full execution-system test runner is implemented and green, and this phase now also closes the execution-system path naming unification across scripts and docs)
