# 汇报版执行系统流程图

## 1. 用途

这份文档面向汇报、评审和交接，不追求把所有脚本节点一次性展开，而是把完整执行系统压缩成 3 张更易讲解的图：

- 总览图：系统从请求进入到交付输出的主链
- 需求分解图：自然语言需求如何落成 `demand / roadmap / tasks / ACTIVE`
- 执行交付图：checks、closeout、handoff 如何形成可验证闭环

如果需要工程级细图，继续看：

- `complete-execution-flow.md`

## 2. 汇报总览图

```mermaid
flowchart LR
    U["用户请求<br/>新需求 / 恢复 / 查询"] --> R["规则入口<br/>skills/six-layer-execution-system/SKILL.md"]
    R --> G{"请求类型"}

    G -->|恢复 / 查询| A["ACTIVE.md<br/>唯一运行态真相"]
    G -->|新自然语言需求| D["需求分解引擎"]
    G -->|系统盘点| I["Inspect 快照"]

    D --> P["生成执行工件<br/>demand / roadmap / tasks / activity"]
    A --> X["按 focus activity 执行"]
    P --> X
    I --> O["状态输出"]

    X --> C["Canonical Checks"]
    C --> H{"是否可 closeout"}
    H -->|否| O
    H -->|是| Z["Closeout Artifact"]
    Z --> F["Handoff Payload"]
    F --> O["状态 / 结果 / 交接输出"]
```

## 3. 需求分解汇报图

```mermaid
flowchart TD
    N["自然语言需求"] --> C0["exec_sys.py demand decompose"]
    C0 --> C1["decomposition_engine.py"]

    C1 --> S1["规范化标题与 slug"]
    C1 --> S2["推断 task_type / risk_level"]
    C1 --> S3["提取 constraints / non_goals"]
    C1 --> S4["生成 3 段切片<br/>A1 -> B1 -> C1"]

    S1 --> W1["写 activities/&lt;id&gt;/0-demand.md"]
    S2 --> W2["写 activities/&lt;id&gt;/2-roadmap.md"]
    S3 --> W3["写 activities/&lt;id&gt;/3-tasks/*.md"]
    S4 --> W4["写 ACTIVE activity"]

    W1 --> B["形成可恢复 backlog 基线"]
    W2 --> B
    W3 --> B
    W4 --> B

    B --> A{"是否 --activate"}
    A -->|是| AF["切 focus 到新 activity"]
    A -->|否| NF["保留当前 focus"]
```

## 4. 执行与交付汇报图

```mermaid
flowchart TD
    S["当前 focus activity<br/>或新生成 activity"] --> K["run_execution_system_checks.py"]
    K --> H1["Hard-fail checkers"]
    K --> H2["Advisory checker"]
    K --> H3["Repo smoke tests<br/>可用时执行"]
    H1 --> R["统一 summary footer + telemetry"]
    H2 --> R
    H3 --> R

    R --> G{"满足 closeout-ready 吗"}
    G -->|否| X["返回失败原因 / 恢复提示"]
    G -->|是| C["complete_slice.py"]

    C --> A1["create_slice_closeout.py"]
    A1 --> A2["local-state/last-slice-closeout.json"]
    A2 --> A3["build_slice_handoff.py"]
    A3 --> O["Handoff Payload / 最终输出"]
```

## 5. 讲解口径

- 第一张图用于讲“系统边界”和“主链闭环”。
- 第二张图用于讲“新增能力”，也就是自然语言需求自动分解。
- 第三张图用于讲“为什么这套系统是生产级的”，因为它不是只生成文档，而是带 checks、ready gate、closeout artifact 和 handoff payload。

## 6. 与真实代码的对应关系

| 汇报节点 | 真实实现 |
| --- | --- |
| 规则入口 | `skills/six-layer-execution-system/SKILL.md` |
| 运行态真相 | `ACTIVE.md` |
| 需求分解引擎 | `scripts/exec_sys.py`、`scripts/decomposition_engine.py`、`scripts/demand_card.py` |
| checks | `scripts/run_execution_system_checks.py`、`scripts/execution_system_suite.py` |
| closeout | `scripts/complete_slice.py`、`scripts/create_slice_closeout.py` |
| handoff | `scripts/build_slice_handoff.py` |
| inspect | `scripts/execution_system_snapshot.py`、`scripts/inspect_execution_system.py` |
