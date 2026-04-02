# execution system decomposition upgrade roadmap

## Goal
- 将 execution system 从“强执行账本”升级为“可分解、可调度、可校验、可恢复”的需求分解引擎。
- 在不破坏 `ACTIVE.md` 单一运行时真相与 focus-first 约束的前提下，引入 demand intake、依赖图、并行波次与分解质量校验。

## Contract reference
- `docs/execution-system-spec-v1.md`
- `docs/execution-system-decomposition-upgrade-plan.md`
- `docs/execution-system-spec-v1-acceptance-checklist.md`

## Validation baseline
- `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_checks.py`
- `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_full_tests.py`
- 不引入第二份 runtime truth
- 不破坏 focus-first 与现有 closeout 语义

## Phases

### Phase 1 - Demand Intake schema
- objective:
  - 为复杂需求引入标准化 intake 模型，避免需求直接跳进 roadmap/tasks
- dependencies:
  - `docs/execution-system-decomposition-upgrade-plan.md`
- outputs:
  - demand intake section in spec
  - demand-card template or equivalent reference
  - task-type taxonomy
- exit criteria:
  - 复杂需求具备统一入口 schema
  - intake 结果可映射到 contract / roadmap / tasks / ACTIVE
- decomposition_strategy:
  - 先落 spec 与模板中的最小 schema，不引入独立 checker 或真实 runtime state 变更
- recommended_wave_shape:
  - `serial`
- risks:
  - intake 设计过重，导致简单任务也被强制文档化

### Phase 2 - Contract and roadmap decomposition guards
- objective:
  - 让 contract 与 roadmap 显式描述“如何拆”与“如何分波次”
- dependencies:
  - Phase 1
- outputs:
  - contract decomposition guardrails
  - roadmap decomposition strategy
  - roadmap recommended wave shape
- exit criteria:
  - contract/roadmap 能表达允许的 slice 形状、依赖形状、波次建议
- decomposition_strategy:
  - 先统一 schema 与模板，再用升级 roadmap 自举验证字段设计是否够用
- recommended_wave_shape:
  - `serial`
- risks:
  - roadmap 过度承载运行态信息

### Phase 3 - Task DAG schema
- objective:
  - 把 tasks 从 slice 清单升级为可检查的 DAG 定义
- dependencies:
  - Phase 2
- outputs:
  - `depends_on`
  - `parallel_safe`
  - `shared_write_targets`
  - `expected_artifacts`
  - `integration_notes`
  - `handoff_output`
- exit criteria:
  - migrated slices 能显式表达依赖与并行安全属性
- decomposition_strategy:
  - 先把 DAG 字段落进 spec/templates/tasks backlog，再用 dependency-graph / parallel-safety checker 做第一批 enforcement
- recommended_wave_shape:
  - `serial`
- risks:
  - schema 过宽，导致填写负担高于收益

### Phase 4 - ACTIVE wave-state model
- objective:
  - 让 `ACTIVE.md` 中的 roadmap activity 具备波次级调度视图
- dependencies:
  - Phase 3
- outputs:
  - `execution_mode`
  - `current_wave_id`
  - `ready_slices`
  - `inflight_slices`
  - `blocked_slices`
  - `integration_step`
  - `last_wave_result`
- exit criteria:
  - heartbeat/manual execution 可基于 ACTIVE 波次状态恢复与调度
  - 至少一个低风险 pilot activity 在真实 `ACTIVE.md` 上通过 `check_active_wave_state.py`
- decomposition_strategy:
  - 先落 schema，再用 decomposition-upgrade activity 自举成低风险 pilot，不急于马上接入 unified runner
- recommended_wave_shape:
  - `parallel-wave`
- risks:
  - ACTIVE 变厚，破坏 lean runtime truth 目标

### Phase 5 - Checker and workflow adoption
- objective:
  - 把新分解模型接入 checker、runner、acceptance 与真实试点 activity
- dependencies:
  - Phases 1-4
- outputs:
  - dependency-graph checker
  - parallel-safety checker
  - active-wave-state checker
  - parallel-wave path test
  - acceptance and runner integration
- exit criteria:
  - 第一批 checker cut 与 pilot path 已明确排序
  - active-wave-state pilot 已写回 acceptance/testing docs
  - 已明确 active-wave-state checker 何时接入 unified runner
  - 至少一个真实 activity 完成 parallel-wave -> integration -> validation -> closeout 闭环
- decomposition_strategy:
  - 先完成 first checker cut 与 pilot docs closeout，再决定 active-wave-state checker 的 runner 集成与 parallel-wave path test 的落地顺序
- recommended_wave_shape:
  - `parallel-wave`
- risks:
  - 过早硬编码未稳定的 schema 或执行策略

## Current recommended phase
- Phase 5 - Checker and workflow adoption (`DX-E.E10` is the handoff closeout: execution-system-decomposition-upgrade keeps its recovery path, while immediate implementation focus returns to `one-publish-refactor`)
