# Decision: one-publish keeps publish runtime split for the last stage

- date: 2026-03-13
- project: one-publish
- status: accepted

## Context
- `one-publish` 第一轮重构的目标是低风险纯拆分，不改行为。
- 前端壳层、hooks、cards、辅助逻辑存在大量独立且更安全的收口机会。
- 后端 publish runtime 涉及运行态单例、cancel、log streaming 等高风险行为。

## Options considered
- A. 一开始就拆 publish runtime，快速触碰核心复杂度
- B. 先持续做前端 shell collapse 和中低风险模块拆分，最后再进入 publish runtime
- C. 同时推进前端壳层拆分和 publish runtime 拆分

## Chosen
- 采用 B：publish runtime 作为最后阶段处理。

## Why
- 先吃掉低风险、可验证、可回滚的切片，能稳定降低复杂度并积累边界认知。
- 等前端壳层与辅助逻辑足够清晰后，再碰 publish runtime，风险更可控。
- 这与 contract 中的“不改行为、不混高低风险改动”一致。

## Rejected because
- A 太激进，容易在缺少边界整理的情况下直接进入高风险核心。
- C 会让问题混在一起，难以定位回归，也不利于小步 closeout。

## Review trigger
- 如果 Phase 5 前端壳层已基本稳定，且 publish runtime 的边界与验证口径足够清晰，则可重新评估进入 runtime split 的时机。
