#!/usr/bin/env python3
from __future__ import annotations

from scripts.decomposition_engine import derive_title, infer_risk_level, infer_task_type, plan_request
from scripts.demand_card import build_project_code, slugify


def expect_equal(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name} drifted\nactual={actual!r}\nexpected={expected!r}")


def main() -> int:
    expect_equal("derive-title-explicit", derive_title("ignored request", "Add execution-system demand"), "Add execution-system demand")
    expect_equal(
        "derive-title-from-request",
        derive_title("实现一个自动分解需求的命令，并保持 ACTIVE 为唯一运行态真相。"),
        "实现一个自动分解需求的命令，并保持 ACTIVE 为唯一运行态真相",
    )
    expect_equal("infer-task-type-docs", infer_task_type("请帮我补一份 code wiki 文档"), "docs")
    expect_equal("infer-task-type-testing", infer_task_type("补一组 smoke tests"), "testing")
    expect_equal("infer-task-type-default", infer_task_type("新增一个命令行生成器"), "implementation")
    expect_equal("infer-risk-level-high", infer_risk_level("生产数据库 schema 迁移"), "high")
    expect_equal("infer-risk-level-medium", infer_risk_level("重构 execution-system workflow"), "medium")
    expect_equal("slugify-ascii", slugify("Add Demand Generator"), "add-demand-generator")
    expect_equal("slugify-fallback-stable", slugify("自动分解需求"), slugify("自动分解需求"))
    expect_equal(
        "slugify-fallback-request",
        slugify("自动分解需求", fallback_text="Generate demand roadmap tasks"),
        "generate-demand-roadmap-tasks",
    )
    expect_equal("project-code", build_project_code("add-demand-generator"), "AD-A")

    docs_plan = plan_request("请补一份 code wiki 文档，并保持 ACTIVE 为唯一运行态真相。", title="Code wiki docs")
    expect_equal("docs-strategy", docs_plan.strategy, "light-delivery")
    expect_equal("docs-slice-count", len(docs_plan.slices), 2)
    expect_equal("docs-manual-review", docs_plan.manual_review_required, False)

    implementation_plan = plan_request(
        "实现一个自动分解需求的命令，并保持 ACTIVE 为唯一运行态真相。",
        title="Demand generator",
    )
    expect_equal("implementation-strategy", implementation_plan.strategy, "implementation-standard")
    expect_equal("implementation-slice-count", len(implementation_plan.slices), 4)
    expect_equal("implementation-next-slice", implementation_plan.next_slice_id.endswith(".B1"), True)

    high_risk_plan = plan_request(
        "实现一个生产数据库 schema 迁移的全自动能力，并直接激活。",
        title="Production migration",
    )
    expect_equal("high-risk-strategy", high_risk_plan.strategy, "implementation-review-gate")
    expect_equal("high-risk-slice-count", len(high_risk_plan.slices), 5)
    expect_equal("high-risk-manual-review", high_risk_plan.manual_review_required, True)

    readable_slug_plan = plan_request(
        "新增 demand roadmap tasks closeout 报告链路，并保持 ACTIVE 为唯一运行态真相。",
        title="真实需求演练报告链路",
    )
    if readable_slug_plan.slug.startswith("request-"):
        raise AssertionError(f"mixed-language request should produce a readable slug\n{readable_slug_plan.slug}")

    explicit_slug_plan = plan_request(
        "新增一条真实需求演练链路，并保持 ACTIVE 为唯一运行态真相。",
        title="真实需求演练报告链路",
        slug="realistic-demand-report",
    )
    expect_equal("explicit-slug", explicit_slug_plan.slug, "realistic-demand-report")
    expect_equal("explicit-slug-activity", explicit_slug_plan.activity_id, "auto-realistic-demand-report")

    deduped_guardrail_plan = plan_request(
        "只允许改生成链路相关脚本和文档，不要重写现有 closeout 协议，不要改动 ACTIVE 里已有活动。",
        title="Guardrail split",
    )
    if set(deduped_guardrail_plan.constraints) & set(deduped_guardrail_plan.non_goals):
        raise AssertionError(
            "constraints and non_goals should not duplicate the same extracted line\n"
            f"constraints={deduped_guardrail_plan.constraints}\n"
            f"non_goals={deduped_guardrail_plan.non_goals}"
        )

    print("DECOMPOSITION_ENGINE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
