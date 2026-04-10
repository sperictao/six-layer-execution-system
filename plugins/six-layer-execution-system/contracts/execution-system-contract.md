# execution system contract

## Scope
- 该 contract 只约束插件根目录下的 six-layer execution system 本体。
- 它定义稳定约束，不记录当前 slice、即时进展或历史叙述。

## Stable constraints
- 插件根目录是默认且唯一的 execution runtime root；不得把 `workspace/`、`runtime/`、`old_version/` 或其它并行目录重新引入为第二运行真相。
- `ACTIVE.md` 是唯一运行态真相；`roadmaps/`、`tasks/`、`decisions/`、`memory/` 只能提供恢复与设计上下文，不能替代 `ACTIVE.md` 回答当前执行状态。
- `skills/six-layer-execution-system/SKILL.md` 是唯一 prompt 规则真相源；恢复顺序、resume trigger 处理、closeout handoff、行为边界与工具入口不得再拆到额外顶层 prompt 文件。
- 默认执行策略是 `focus-first`；非 focus activity 可以并存用于恢复、历史和维护，但不得默认自动推进。
- roadmap activity 一旦声明 `path` 与 `last_commit`，它们就必须在插件根 git repo 内可解析，且 `last_commit` 必须继续接受强校验。
- slice 完成语义必须显式落在 closeout artifact 中；`validation_state=validated` 与 `slice_state=closed_out` 不能退化为隐式约定。
- contract 只保存长期约束；当前 repo 脏状态、临时操作记录、日记式里程碑不得写入 contract。

## Decomposition Guardrails
- allowed_slice_shapes:
  - single-goal normalization slices
  - guardrail or review-gate slices
  - primary delivery slices
  - validation and handoff slices
- forbidden_slice_shapes:
  - slices that mix broad runtime semantics changes with unrelated UI or documentation rewrites
  - slices that mutate `ACTIVE.md` and delivery artifacts without an explicit integration note
- preferred_dependency_shape: serial-first with an explicit review gate for high-risk work
- parallelism_policy: only slices with no shared write targets may run in the same wave
- integration_constraints:
  - generated demand, roadmap, tasks, and ACTIVE activity metadata must pass a cross-artifact consistency check before activation

## Review triggers
- high-risk demands
- `external_confirmation_required=true` demands
- inferred boundaries that still need a human correction before activation

## Validation floor
- 默认入口在无额外 env override 的情况下可运行：
  - `python3 scripts/inspect_execution_system.py --format markdown`
  - `python3 scripts/run_execution_checks.py checks --timeout 60`
  - `python3 scripts/run_execution_checks.py full-tests --timeout 60`
- repo-local 开发测试统一位于 source checkout 根 `tests/`；直接运行单测时使用仓库根视角命令并显式注入 `PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts"`。
- `checks` 必须在 standalone plugin 场景下继续可用；repo smoke tests 缺席时只能报告 `skipped` / `unavailable`，不能把插件本体判成失败。
- `full-tests` 只对带根 `tests/` 的 source checkout 提供完整保证；standalone plugin 副本返回 `unavailable` 属于 contract 允许范围。
- 文档、脚本与 live ledger 不得再默认依赖 `old_version/` 或外部业务 repo。

## Non-goals
- 不为外部业务仓库保存重构策略、验证命令或 repo-specific invariant。
- 不在 contract 中记录当前 focus、下一切片或历史外发状态。
