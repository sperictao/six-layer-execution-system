# Auto decompose natural-language demand roadmap

## Goal
- 将需求 `Auto decompose natural-language demand` 从自然语言请求收敛成可执行 backlog，并保持 execution-system 约束不漂移。

## Contract reference
- `contracts/execution-system-contract.md`

## Source demand
- `demands/2026-04-10-auto-decompose-natural-language-demand.md`

## Validation baseline
- `python3 scripts/check_demand_card_schema.py`
- `python3 scripts/check_generated_decomposition_consistency.py`
- `python3 scripts/run_execution_checks.py checks --timeout 60`

## Phases

### Phase 1 - Demand normalization
- objective:
  - 将高风险请求收敛为可执行目标、约束和最小 review 边界
- dependencies:
  - source demand
- outputs:
  - normalized demand card
  - activity-ready roadmap/tasks shell
- exit criteria:
  - scope, constraints, and the first review boundary are explicit
- decomposition_strategy:
  - normalize-before-review-gate
- recommended_wave_shape:
  - `serial`
- risks:
  - high-risk requests must not widen scope before a human review

### Phase 2 - Review gate and activation policy
- objective:
  - 将 contract guardrails、review triggers 和 activation policy 固化到 backlog 中
- dependencies:
  - Phase 1
- outputs:
  - review gate notes
  - activation policy
- exit criteria:
  - manual review boundary and confirmation gate are explicit
- decomposition_strategy:
  - review-gate-before-primary-delivery
- recommended_wave_shape:
  - `serial`
- risks:
  - activation remains blocked until explicit confirmation is recorded

### Phase 3 - Primary delivery planning
- objective:
  - 为高风险 'implementation' 工作生成主交付切片与依赖链
- dependencies:
  - Phase 2
- outputs:
  - primary delivery slice
  - validation-ready dependency chain
- exit criteria:
  - primary artifacts and dependency shape are explicit
- decomposition_strategy:
  - primary-delivery-after-review-gate
- recommended_wave_shape:
  - `serial`
- risks:
  - generated artifacts must remain serial until the write surface is fully understood

### Phase 4 - Consistency validation
- objective:
  - 确保 generated demand / roadmap / tasks / ACTIVE 活动卡片没有跨工件漂移
- dependencies:
  - Phase 3
- outputs:
  - checker-accepted decomposition baseline
  - confirmation-safe activation boundary
- exit criteria:
  - cross-artifact consistency and graph checks pass
- decomposition_strategy:
  - cross-artifact-consistency-before-activation
- recommended_wave_shape:
  - `serial`
- risks:
  - activation remains blocked if any review or consistency drift remains

### Phase 5 - Handoff readiness
- objective:
  - 确认该高风险 backlog 已具备 handoff-ready 的 review 与 validation 说明
- dependencies:
  - Phase 4
- outputs:
  - handoff-ready activity metadata
  - manual review packet
- exit criteria:
  - canonical checks pass and the review gate is explicit
- decomposition_strategy:
  - handoff-after-explicit-review-boundary
- recommended_wave_shape:
  - `serial`
- risks:
  - autonomous execution must remain disabled until a human explicitly decides otherwise

## Current recommended phase
- Phase 1 - Demand normalization (`AD-A.A1` first)

## Activity anchor
- `auto-auto-decompose-natural-language-demand`
