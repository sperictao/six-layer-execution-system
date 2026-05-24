# 完整执行系统流程图

## 1. 说明

这张图把当前插件里的完整执行链放到一张图里，覆盖：

- 新请求 / 恢复请求 / inspect 请求入口
- `ACTIVE.md` 驱动的 focus-first 恢复链
- 自然语言需求一键分解链
- checks / smoke tests / telemetry 链
- closeout / handoff 链

其中最重要的边界是：

- `ACTIVE.md` 仍然是唯一 live runtime truth
- `activities/<activity-id>/0-demand.md` 是上游 intake 工件，不替代运行态真相
- `activities/<activity-id>/2-roadmap.md` 和 `3-tasks/` 承载执行设计，真正的当前执行状态仍落在 `ACTIVE.md`

如果需要更适合汇报的简化视图，见：

- `executive-flow-views.md`

## 2. 完整流程图

```mermaid
flowchart TD
    subgraph INGRESS["1. 入口与恢复分流"]
        U["用户输入<br/>新需求 / 恢复指令 / 状态查询 / inspect"] --> S["读取规则真相<br/>skills/six-layer-execution-system/SKILL.md"]
        S --> T{"请求类型"}
        T -->|恢复 / 状态查询| A["读取 ACTIVE.md<br/>唯一 live runtime truth"]
        T -->|自然语言需求分解| D0["执行 CLI<br/>exec_sys.py demand decompose"]
        T -->|inspect| I0["执行 inspect<br/>inspect_execution_system.py"]
    end

    subgraph RECOVERY["2. Focus-first 恢复与执行入口"]
        A --> A1["active_ledger.parse_ledger()<br/>解析 Ledger meta / Activity index / Activities"]
        A1 --> A2["定位 current_focus_activity_id"]
        A2 --> A3["读取 focus activity 的<br/>source_doc / roadmap_doc / tasks_doc"]
        A3 --> A4["结合 repo/workspace fact check<br/>决定回复内容或下一步动作"]
        A4 --> A5["执行当前 slice<br/>或用 exec_sys.py slice start 更新 current_slice_id"]
    end

    subgraph INSPECT["3. Inspect 快照路径"]
        I0 --> I1["execution_system_snapshot.py<br/>汇总 docs / scripts / skills / ledger"]
        I1 --> I2["输出 Markdown 或 JSON 快照"]
    end

    subgraph DECOMPOSE["4. 需求分解链（新增能力）"]
        D0 --> D1["decomposition_engine.decompose_request()"]
        D1 --> D2["规范化请求<br/>derive_title + slugify + build_project_code"]
        D1 --> D3["推断语义<br/>task_type + risk_level + constraints + non_goals"]
        D1 --> D4["构造 DemandCard"]
        D4 --> D5["demand_card.render_demand_card()<br/>渲染 activities/&lt;id&gt;/0-demand.md"]
        D1 --> D6["生成 roadmap Markdown<br/>Phase / exit criteria / wave shape"]
        D1 --> D7["生成 tasks Markdown<br/>Slice / depends_on / validation / rollback"]
        D1 --> D8["生成 Activity 卡片<br/>current_slice_id / next_slice_id / validation / retrieval_keys"]
        D8 --> D9["Ledger.add_activity()<br/>追加 Activity index 和 Activity block"]
        D5 --> D10["写入 activities/&lt;id&gt;/0-demand.md"]
        D6 --> D11["写入 activities/&lt;id&gt;/2-roadmap.md"]
        D7 --> D12["写入 activities/&lt;id&gt;/3-tasks/*.md"]
        D9 --> D13["更新 ACTIVE.md meta<br/>至少刷新 updated_at"]
        D13 --> D14{"是否使用 --activate"}
        D14 -->|是| D15["切换 current_focus_activity_id<br/>和 default_reply_activity_id"]
        D14 -->|否| D16["保持当前 focus 不变"]
        D10 --> D17["形成可恢复的 demand / roadmap / tasks / ACTIVE 基线"]
        D11 --> D17
        D12 --> D17
        D15 --> D17
        D16 --> D17
    end

    subgraph VALIDATE["5. checks / smoke tests / telemetry"]
        A5 --> C0["执行 checks wrapper<br/>run_execution_checks.py checks"]
        D17 --> C0
        C0 --> C1["plugin_paths.run_root_script()<br/>转发到 run_local_execution_checks.py"]
        C1 --> C2["run_local_execution_checks.py<br/>选择 active / checks / full-tests / closeout-ready"]
        C2 --> C3["run_execution_system_checks.collect_summary()"]
        C3 --> C4["Hard-fail checkers"]
        C4 --> C4A["check_active_consistency.py<br/>ACTIVE 与 focus/activity 一致性"]
        C4 --> C4B["check_demand_card_schema.py<br/>demand intake schema"]
        C4 --> C4C["check_task_slice_schema.py<br/>slice 结构完整性"]
        C4 --> C4D["check_task_dependency_graph.py<br/>依赖引用与 cycle"]
        C4 --> C4E["check_parallel_safety.py<br/>parallel_safe 与 shared_write_targets"]
        C4 --> C4F["check_active_wave_state.py<br/>parallel-wave 状态字段"]
        C4 --> C4G["check_execution_system_governance_consistency.py<br/>spec / skill / recovery 规则对齐"]
        C4 --> C4H["check_execution_system_status_freshness.py<br/>耐久文档状态新鲜度"]
        C3 --> C5["Advisory checker<br/>check_oversized_migration_slices.py"]
        C3 --> C6{"是否识别 source checkout tests<br/>且未开启 agile mode"}
        C6 -->|是| C7["执行 repo smoke tests<br/>tests/test_check_*.py + path tests"]
        C6 -->|否| C8["标记 skipped 或 unavailable<br/>并给出原因"]
        C7 --> C9["生成 summary footer"]
        C8 --> C9
        C5 --> C9
        C9 --> C10["写 telemetry<br/>local-state/telemetry.jsonl"]
    end

    subgraph CLOSEOUT["6. Closeout 与 Handoff"]
        C10 --> H0{"是否进入 slice complete / handoff"}
        H0 -->|否| H1["返回状态、检查结果或 inspect 输出"]
        H0 -->|是| H2["执行 CLI<br/>exec_sys.py slice complete"]
        H2 --> H3["complete_slice.prepare_slice()"]
        H3 --> H4["再次 collect_summary()<br/>确保 hard-fail suite 已通过"]
        H4 --> H5["check_closeout_ready()<br/>检查 focus 类型与 closeout 必要字段"]
        H5 --> H6{"focus 是 roadmap<br/>且 current_slice_id / next_slice_id / last_commit / last_validation 齐全"}
        H6 -->|否| H7["停止并输出 CLOSEOUT_READY_FAILED"]
        H6 -->|是| H8["create_slice_closeout.py<br/>生成 frozen closeout artifact"]
        H8 --> H9["写入 local-state/last-slice-closeout.json"]
        H9 --> H10["build_slice_handoff.py<br/>从 frozen artifact 构建 payload"]
        H10 --> H11["输出 handoff payload<br/>供下游 host 或后续流程消费"]
    end
```

## 3. 节点与代码映射

| 流程节点 | 真实实现 |
| --- | --- |
| 账本解析 | `scripts/active_ledger.py` |
| inspect 快照 | `scripts/execution_system_snapshot.py`、`scripts/inspect_execution_system.py` |
| 需求分解入口 | `scripts/exec_sys.py` |
| 需求分解引擎 | `scripts/decomposition_engine.py` |
| demand schema / 渲染 | `scripts/demand_card.py`、`scripts/check_demand_card_schema.py` |
| checks runner | `scripts/run_execution_checks.py`、`scripts/run_local_execution_checks.py`、`scripts/run_execution_system_checks.py` |
| suite 注册表 | `scripts/execution_system_suite.py` |
| closeout / handoff | `scripts/complete_slice.py`、`scripts/create_slice_closeout.py`、`scripts/build_slice_handoff.py` |
| full suite | `scripts/run_execution_system_full_tests.py` |

## 4. 读图重点

- 如果入口是“恢复 / 继续”，系统先走 `ACTIVE.md`，不是先看 roadmap。
- 如果入口是“新自然语言需求”，系统先生成 `activities/<activity-id>/ + ACTIVE activity`，再进入 canonical checks。
- `--activate` 只影响 focus 切换，不改变 demand/roadmap/tasks 的生成结构。
- `closeout` 不直接依赖实时 `ACTIVE.md` 输出 payload，而是先冻结到 `local-state/last-slice-closeout.json`，再从 frozen artifact 生成 handoff。
