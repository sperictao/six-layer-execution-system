# execution system testing tasks

## Current phase
- Phase 5 - Unified full-test entrypoint (`ET-E / Slice E1 - add unified execution-system full-test runner`)

## PR queue

### ET-A - testing foundation inventory
- goal:
  - 建立 execution-system 测试体系的完整分层图与缺口清单
- validation:
  - 测试分层清楚
  - 已有 smoke / semantic / execution-system path / governance coverage 列表化
- done_definition:
  - 完整测试路线图与任务分解落盘
- risk:
  - low

#### Slice A1 - inventory existing execution-system tests and gaps
- phase_id: `PH-1`
- goal:
  - 盘点当前已存在的 execution-system 测试与验收入口，并明确缺口
- scope:
  - `docs/`
  - `scripts/`
  - `roadmaps/execution-system-testing-roadmap.md`
  - `tasks/execution-system-testing-tasks.md`
- target_files:
  - `roadmaps/execution-system-testing-roadmap.md`
  - `tasks/execution-system-testing-tasks.md`
  - `docs/execution-system-spec-v1-acceptance-checklist.md`
  - `docs/execution-system-testing-inventory.md`
- depends_on:
  - none
- validation:
  - 已有测试按 layout / semantics / smoke / execution-system path / governance 分类
  - 缺口列表明确
- done_definition:
  - execution-system 完整测试 backlog 已冻结
- rollback_strategy:
  - revert inventory docs if they become vague planning prose instead of executable testing backlog
- risk:
  - low

### ET-B - semantic coverage strengthening
- goal:
  - 增强 execution-system 的语义单测与 smoke 组织度
- validation:
  - checker / advisory / closeout / summary 语义测试职责清晰
- done_definition:
  - 关键语义测试簇成型
- risk:
  - medium

#### Slice B1 - normalize execution-system semantic tests
- phase_id: `PH-2`
- goal:
  - 统一现有 semantic / smoke 测试的命名、职责与入口
- scope:
  - `scripts/`
  - `tasks/execution-system-testing-tasks.md`
- target_files:
  - `scripts/test_check_active_consistency.py`
  - `scripts/test_check_task_slice_schema.py`
  - `scripts/test_check_oversized_migration_slices.py`
  - `scripts/test_run_execution_system_checks.py`
  - `scripts/test_slice_closeout_state.py`
- depends_on:
  - `ET-A.A1`
- validation:
  - 每个测试文件职责单一且命名清楚
- done_definition:
  - execution-system 语义测试簇结构清晰
- rollback_strategy:
  - revert reorganizations if they make current smoke coverage harder to run or understand
- risk:
  - medium

### ET-C - execution-system path matrix coverage
- goal:
  - 为 execution system 的关键路径建立矩阵测试
- validation:
  - 关键路径与负路径均有链路测试
- done_definition:
  - execution-system path matrix 初步完整
- risk:
  - medium

#### Slice C1 - hard-fail execution-system path test
- phase_id: `PH-3`
- goal:
  - 为 hard-fail 路径补一条链路测试
- scope:
  - `scripts/`
  - `tasks/execution-system-testing-tasks.md`
- target_files:
  - `scripts/test_execution_system_path_hard_fail.py`
- depends_on:
  - `ET-A.A1`
- validation:
  - runner fail / summary fail / closeout-ready fail / acceptance fail 路径被覆盖
- done_definition:
  - hard-fail execution-system path 可回归测试
- rollback_strategy:
  - revert if test relies on brittle workspace mutations rather than controlled fixtures
- risk:
  - medium

#### Slice C2 - policy-gate execution-system path test
- phase_id: `PH-3`
- goal:
  - 为 policy-gate 路径补一条链路测试
- scope:
  - `scripts/`
- target_files:
  - `scripts/test_execution_system_path_policy_gate.py`
- depends_on:
  - `ET-C.C1`
- validation:
  - focus-first policy gate 与 acceptance ok-with-policy-gates 被同时覆盖
- done_definition:
  - policy-gate execution-system path 可回归测试
- rollback_strategy:
  - revert if test hides real focus-first failures behind over-broad gate mocking
- risk:
  - medium

#### Slice C3 - closeout-blocked execution-system path test
- phase_id: `PH-3`
- goal:
  - 为 closeout-ready 被阻断的路径补一条链路测试
- scope:
  - `scripts/`
- target_files:
  - `scripts/test_execution_system_path_closeout_blocked.py`
- depends_on:
  - `ET-C.C2`
- validation:
  - hard-fail pass 但 closeout-ready fail 的路径被覆盖
- done_definition:
  - closeout-blocked execution-system path 可回归测试
- rollback_strategy:
  - revert if blocked-path setup becomes coupled to unstable workspace details
- risk:
  - medium

#### Slice C4 - focus-switch execution-system path test
- phase_id: `PH-3`
- goal:
  - 为 focus switch 相关路径补正式链路测试
- scope:
  - `scripts/`
  - `ACTIVE.md`
- target_files:
  - `scripts/test_execution_system_path_focus_switch.py`
- depends_on:
  - `ET-C.C3`
- validation:
  - 从 execution-system maintenance focus 切回业务 focus 时，runner / acceptance / smoke 都不假红
- done_definition:
  - focus-switch path 可回归测试
- rollback_strategy:
  - revert if test mutates ledger state in a way that is not safely restored
- risk:
  - medium

### ET-D - governance and maintenance checks
- goal:
  - 为 maintenance mode / reopen / re-entry 提供轻量治理测试
- validation:
  - 治理语义具备最小一致性检查
- done_definition:
  - 执行系统治理层不再完全依赖人工记忆
- risk:
  - low-to-medium

#### Slice D1 - maintenance mode consistency check
- phase_id: `PH-4`
- goal:
  - 检查 execution-system parked / maintenance posture 与当前 business focus 是否一致
- scope:
  - `ACTIVE.md`
  - `scripts/`
- target_files:
  - `scripts/check_execution_system_maintenance_mode.py`
- depends_on:
  - `ET-A.A1`
- validation:
  - execution-system parked + business focus runnable + acceptance green 能同时成立
- done_definition:
  - maintenance-mode consistency 可自动检查
- rollback_strategy:
  - revert if the checker becomes too tied to one workspace state instead of the maintenance-mode rule itself
- risk:
  - low

#### Slice D2 - reopen / re-entry consistency check
- phase_id: `PH-4`
- goal:
  - 轻量检查 spec / roadmap / tasks / ACTIVE 对 reopen / re-entry 语义是否一致
- scope:
  - `docs/`
  - `roadmaps/`
  - `tasks/`
  - `ACTIVE.md`
- target_files:
  - `scripts/check_execution_system_governance_consistency.py`
- depends_on:
  - `ET-D.D1`
- validation:
  - reopen conditions 与 re-entry protocol 在多处描述不互相矛盾
- done_definition:
  - execution-system 治理语义具备最小一致性校验
- rollback_strategy:
  - revert if the check becomes brittle text matching instead of meaningful semantic consistency
- risk:
  - medium

### ET-E - unified full-test entrypoint
- goal:
  - 把 execution-system 完整测试矩阵汇总为统一入口与文档化回执
- validation:
  - 一键运行全量 execution-system tests
  - 输出区分 fail / advisory / policy-gate / governance review
- done_definition:
  - execution-system full-test suite 成型
- risk:
  - medium

#### Slice E1 - add unified execution-system full-test runner
- phase_id: `PH-5`
- goal:
  - 汇总 execution-system 全量测试为统一入口，并收口 execution-system path 命名
- scope:
  - `scripts/`
  - `docs/`
- target_files:
  - `scripts/run_execution_system_full_tests.py`
  - `scripts/test_execution_system_path_*.py`
  - `docs/execution-system-testing-inventory.md`
  - `roadmaps/execution-system-testing-roadmap.md`
  - `tasks/execution-system-testing-tasks.md`
- depends_on:
  - `ET-C.C4`
  - `ET-D.D2`
- validation:
  - 可一次运行当前 execution-system 全量测试矩阵
  - `python3 /Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_full_tests.py` 通过
  - execution-system path 命名在 roadmap/tasks/inventory/full-test runner 中一致
- done_definition:
  - 完整测试入口可运行并产出可读回执
  - execution-system path 测试文件与文档口径已统一
- rollback_strategy:
  - revert if the full-test runner becomes harder to diagnose than the individual tests it aggregates
- risk:
  - medium
