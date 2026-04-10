---
name: six-layer-execution-system
description: Inspect, explain, validate, repair, or port a focus-first six-layer execution-system repository whose root stores runtime truth, checker suites, closeout flows, and a single skill-owned prompt protocol.
---

# Six-Layer Execution System

Use this skill when the task is about a repository that follows the six-layer execution-system layout.

## Prompt Authority

- `skills/six-layer-execution-system/SKILL.md` is the only prompt-rule source of truth for this plugin.
- `ACTIVE.md` remains the only live runtime truth.
- `memory/working-buffer.md` is only a recovery buffer, never runtime truth.
- Repo-local development tests live under the source checkout root `tests/`.
- Standalone plugin copies do not carry repo-root `tests/`.

Treat the current repository as the subject:

- the repository root stores runtime truth, docs, scripts, and skills
- `references/` stores helper docs and source maps
- `scripts/inspect_execution_system.py` and `scripts/run_execution_checks.py` are the plugin-safe wrapper commands

## Quick Start

Follow this order unless the task is clearly narrower:

1. Run `python3 scripts/inspect_execution_system.py --format markdown`.
2. Read `ACTIVE.md`.
3. Resolve the current focus activity and its `source_doc`, `roadmap_doc`, and `tasks_doc`.
4. Read `references/checkers-and-protocols.md` if the task touches validation or closeout.
5. Read `references/workspace-execution-system.md` for local conventions.
6. Read `references/local-install.md` only if the task touches wrapper behavior, local installation, or upstream runtime handoff.
7. Use `references/source-map.md` when you need exact file pointers before opening original files.

If you need to point these entrypoints at another extracted repo, override `SIX_LAYER_REPO_ROOT` and `SIX_LAYER_WORKSPACE` before running them.

## Recovery And Resume Triggers

Short imperative or resume-like messages must be treated as execution recovery, not general chat.

Examples:

- `go`
- `continue`
- `继续`
- `resume`
- `next`
- `start`
- `where were we`
- `what were we doing`

Required recovery sequence:

1. read `memory/working-buffer.md` first when it exists
2. read `ACTIVE.md`
3. resolve `current_focus_activity_id`
4. read the focus activity card
5. if it is a roadmap activity, read its linked roadmap/tasks docs
6. inspect repo/workspace facts before replying or acting

Forbidden recovery shortcuts:

- do not infer current state from old memory notes alone
- do not assume roadmap == current state
- do not auto-run a non-focus activity
- do not answer task-status or task-resume questions from conversational memory alone when `ACTIVE.md` exists as execution truth

## Resume And Closeout Handoff Protocol

- 恢复型触发必须遵守同一套恢复规则；不得跳过 `ACTIVE.md` / focus activity / roadmap/tasks / repo fact check 这些步骤
- 对 `go` / `continue` / `继续` / `resume` / `next` / `start` 这类恢复型触发来说：若 `memory/working-buffer.md` 存在，先读它；然后读 `ACTIVE.md`；再读 focus activity card；再读 roadmap/tasks；最后做 repo/workspace fact check，之后才能汇报进度或继续执行
- 恢复型触发不得仅凭聊天记忆、旧 daily note 推断当前任务状态；工作空间执行文件优先于会话推断
- 恢复型触发后的执行规划必须与人工执行遵守同一套并行调度口径
- 将无前置依赖、且无写冲突的子任务按同一波次并行处理
- 若存在硬依赖链、共享写目标、或后续决策依赖前一步输出，则必须保持串行
- 只有 current focus activity 可以进入自动执行路径；非 focus activities 只用于恢复、提醒、展示状态，不得擅自推进

Active work check:

- 先运行 `python3 scripts/run_execution_checks.py checks --timeout 60`
- 如果当前只是 standalone plugin 副本、没有 source checkout 根 `tests/`：允许 `run_execution_system_checks.py` 报告 repo smoke tests `skipped` / `unavailable`；这不等于 checker hard-fail
- 不要把 `run_execution_system_full_tests.py` 在 standalone plugin 副本里的 `unavailable` 误判成运行时故障；只有在 source checkout 场景下，它才是完整 suite 入口
- 如果统一 checker 套件失败：先定位失败子命令，再按当前 focus 收敛根因；未修复前不要把状态汇报成绿色

Closeout and handoff rules:

- `scripts/complete_slice.py` is the canonical closeout entrypoint
- `scripts/build_slice_handoff.py` prints the canonical handoff payload from the frozen closeout artifact
- `payload` output must be derived from `memory/last-slice-closeout.json`, not from live `ACTIVE.md` fields
- if validation passed but `scripts/check_slice_closeout.py` failed, treat the slice as not closed out

## Long-Term Context And Preferences

User and working preferences for this repository:

- 默认中文回复
- 涉及执行系统状态、进展或恢复问题时，先查 `ACTIVE.md`、相关 tasks/roadmap、repo 事实，再回答
- 复杂任务优先维护 `roadmap + tasks`；`ACTIVE.md` 只保留当前运行真相与恢复指针
- 对进行中的项目，优先维护一份可恢复的活动任务账本
- 回答“结果怎么样了 / 进展如何”这类问题前，先检查 `ACTIVE.md`、`memory/YYYY-MM-DD.md`、当前 skill，以及最近会话转录（若可用）

Continuity model:

- 跨会话连续性来自 `ACTIVE.md`、`memory/`、durable docs、以及当前 skill，不是模型记忆
- 长期约定直接收敛到当前 skill，不再拆到单独的记忆 prompt 文件
- 如果发生会影响执行判断的重要决定但尚未落盘，优先写回 `ACTIVE.md` 或 owning docs

## Behavior Style And Boundaries

- 事实优先，不靠聊天记忆编造当前状态
- 先读文件、跑检查、看 repo 事实，再下判断
- 表达保持简洁、明确、可验证，不写表演式客套
- 改动优先追求收口、减漂移、减双重真相，而不是扩大系统边界
- 不把外部业务仓库、个人助理规则、社交平台规则混进 execution-system 本体
- 不在未确认的情况下执行破坏性操作或对外发送动作
- 对协议面改动，优先同步脚本、测试、文档和 acceptance 面
- 能薄封装解决的问题，不引入新平台层

## Tool Facts And Validation Entrypoints

Default entrypoints:

- `python3 scripts/inspect_execution_system.py --format markdown`
- `python3 scripts/run_execution_checks.py active --timeout 60`
- `python3 scripts/run_execution_checks.py checks --timeout 60`
- `python3 scripts/run_execution_checks.py full-tests --timeout 60`

Validation rules:

- ordinary implementation or doc changes default to `checks`
- protocol, governance, closeout, handoff, or runner changes require `full-tests`
- `full-tests` requires the source checkout with repo-root `tests/` present
- direct repo-local test commands run from the repository root with `PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts"`

Path and tool ownership facts:

- local runtime root: `<plugin-root>`
- repo-local development tests root: `<repo-root>/tests`
- local install snapshot belongs in `references/local-install.md`
- agent runtime architecture belongs in `references/agent-runtime.md`
- live runtime truth belongs in `ACTIVE.md`

## Task Flows

### Explain Or Audit The System

1. Run `python3 scripts/inspect_execution_system.py --format markdown`.
2. Read `ACTIVE.md` and `references/workspace-execution-system.md`.
3. Read `references/agent-runtime.md` only if the question actually depends on agent runtime mechanics or plugin installation.
4. Open original files only for the area you need to quote or modify.

### Recover Current Execution State

1. Read `memory/working-buffer.md` when it exists.
2. Read `ACTIVE.md`.
3. Resolve the current focus activity and its linked docs.
4. Verify repository and workspace facts before reporting status.
5. Read daily notes only after runtime truth is loaded.

### Modify The Execution System

1. Decide which layer owns the requested change.
2. Before adding a new field or protocol surface, check whether an existing field already carries the same semantics.
3. If the user still requires a new explicit field name, add it without removing the old one, then update every downstream surface in one pass.
4. Edit only the owning layer plus any directly dependent validators or tests.
5. If the change affects recovery, resume trigger handling, prompt protocol, or behavioral rules, inspect this skill, the owning spec, and the related checker/tests together.
6. If the change affects closeout semantics, inspect:
   - `scripts/complete_slice.py`
   - `scripts/build_slice_handoff.py`
   - `scripts/create_slice_closeout.py`
   - `scripts/check_slice_closeout.py`
   - `scripts/check_closeout_ready.py`
7. If the change affects parallel-wave semantics, inspect:
   - `scripts/check_task_dependency_graph.py`
   - `scripts/check_parallel_safety.py`
   - `scripts/check_active_wave_state.py`

### Pick The Right Validation Shape

1. If you changed one artifact field, one checker rule, or one payload field, run the nearest smoke test first.
2. If you changed a value that must survive across multiple surfaces, add or update a synthetic path test that walks the whole chain.
3. If you changed what the system claims is required for acceptance, update the acceptance checklist wording in the same slice.
4. If you changed runner composition or protocol behavior, rerun `full-tests`, not just `checks`.

Typical mapping:

- artifact field only -> repo-local `tests/test_slice_closeout_state.py`
- checker gate only -> the nearest repo-local `tests/test_check_*.py`
- artifact -> payload propagation -> add or update repo-local `tests/test_execution_system_path_*`
- governance or prompt-rule drift -> `tests/test_execution_system_governance_consistency.py` and `tests/test_execution_system_path_governance_drift.py`
- acceptance contract wording -> update `docs/execution-system-spec-v1-acceptance-checklist.md`

## Resources

- `ACTIVE.md`: live runtime truth
- `references/workspace-execution-system.md`: local six-layer model and maintenance semantics
- `references/checkers-and-protocols.md`: checker, advisory, full-suite, and closeout pipeline map
- `references/source-map.md`: exact file path index for the local repository
- `references/local-install.md`: plugin runtime surface and installed assets
- `references/agent-runtime.md`: agent runtime, plugin installation, and environment variable reference
- `scripts/inspect_execution_system.py`: inspect the execution system plugin state and ledger
- `scripts/run_local_execution_checks.py`: call the canonical local checker and full-test entrypoints with a bounded timeout
- `scripts/run_execution_checks.py`: plugin wrapper for the validation entrypoint
