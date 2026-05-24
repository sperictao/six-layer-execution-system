#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

from active_ledger import Activity, parse_ledger
from demand_card import (
    DemandCard,
    build_project_code,
    render_demand_card,
    sanitize_inline,
    slugify,
)
from execution_system_paths import ACTIVE_PATH, WORKSPACE

CONTRACT_DOC = "docs/execution-system-spec-v1.md"
VALIDATION_CHECKS_COMMAND = "python3 scripts/run_execution_checks.py checks --timeout 60"
DEMAND_SCHEMA_COMMAND = "python3 scripts/check_demand_card_schema.py"
CONSISTENCY_COMMAND = "python3 scripts/check_generated_decomposition_consistency.py"
DEPENDENCY_COMMAND = "python3 scripts/check_task_dependency_graph.py"
PARALLEL_COMMAND = "python3 scripts/check_parallel_safety.py"
ACTIVATION_CONFIRMATION_REASON = "explicit confirmation required before activation"
MANUAL_REVIEW_REASON = "manual review required before autonomous execution"
MANUAL_REVIEW_OR_CONFIRM_REASON = "manual review or explicit confirmation required before activation"


@dataclass(frozen=True)
class DecompositionResult:
    title: str
    task_type: str
    risk_level: str
    strategy: str
    activity_id: str
    demand_doc: str
    roadmap_doc: str
    tasks_doc: str
    current_slice_id: str
    next_slice_id: str
    status: str
    autopilot: bool
    activated: bool
    confirmation_required_for_activation: bool
    activation_blocked_reason: str | None


@dataclass(frozen=True)
class ContractGuardrails:
    allowed_slice_shapes: list[str]
    forbidden_slice_shapes: list[str]
    preferred_dependency_shape: str
    parallelism_policy: str
    integration_constraints: list[str]
    review_triggers: list[str]


@dataclass(frozen=True)
class DemandClassification:
    title: str
    request: str
    task_type: str
    risk_level: str
    external_confirmation_required: str
    constraints: list[str]
    non_goals: list[str]


@dataclass(frozen=True)
class PhasePlan:
    name: str
    objective: list[str]
    dependencies: list[str]
    outputs: list[str]
    exit_criteria: list[str]
    decomposition_strategy: str
    recommended_wave_shape: str
    risks: list[str]


@dataclass(frozen=True)
class SlicePlan:
    short_id: str
    title: str
    phase_id: str
    goal: list[str]
    scope: list[str]
    target_files: list[str]
    depends_on: list[str]
    parallel_safe: bool
    shared_write_targets: list[str]
    expected_artifacts: list[str]
    integration_notes: list[str]
    handoff_output: list[str]
    validation: list[str]
    done_definition: list[str]
    rollback_strategy: list[str]
    risk: str


@dataclass(frozen=True)
class DecompositionPlan:
    title: str
    request: str
    slug: str
    activity_id: str
    project_code: str
    task_type: str
    risk_level: str
    strategy: str
    demand_doc: str
    roadmap_doc: str
    tasks_doc: str
    contract_doc: str
    guardrails: ContractGuardrails
    phases: list[PhasePlan]
    slices: list[SlicePlan]
    current_slice_id: str
    next_slice_id: str
    manual_review_required: bool
    external_confirmation_required: str
    constraints: list[str]
    non_goals: list[str]


DEFAULT_GUARDRAILS = ContractGuardrails(
    allowed_slice_shapes=[
        "single-goal normalization slices",
        "guardrail or review-gate slices",
        "primary delivery slices",
        "validation and handoff slices",
    ],
    forbidden_slice_shapes=[
        "broad runtime semantics changes mixed with unrelated UX or documentation rewrites",
        "slices that mutate ACTIVE and delivery artifacts without an explicit integration note",
    ],
    preferred_dependency_shape="serial-first with an explicit review gate for high-risk work",
    parallelism_policy="only slices with no shared write targets may run in the same wave",
    integration_constraints=[
        "generated demand, roadmap, tasks, and ACTIVE activity metadata must pass a cross-artifact consistency check before activation",
    ],
    review_triggers=[
        "high-risk demands",
        "external_confirmation_required=true demands",
    ],
)

TASK_TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("testing", ("test", "测试", "验证", "smoke", "qa")),
    ("docs", ("文档", "wiki", "readme", "说明", "report", "guide")),
    ("refactor", ("refactor", "重构", "整理", "拆分", "优化结构")),
    ("governance", ("规范", "governance", "协议", "checker", "ledger", "流程")),
    ("coordination", ("发布", "协调", "handoff", "交接", "计划", "排期")),
    ("simple", ("改文案", "rename", "小改", "文案", "颜色")),
)
HIGH_RISK_KEYWORDS = (
    "delete",
    "drop",
    "生产",
    "production",
    "schema",
    "database",
    "db",
    "权限",
    "security",
)
MEDIUM_RISK_KEYWORDS = (
    "refactor",
    "重构",
    "协议",
    "自动化",
    "并行",
    "迁移",
    "workflow",
    "ledger",
    "parser",
)
CONFIRMATION_KEYWORDS = (
    "生产",
    "production",
    "delete",
    "drop",
    "push",
    "commit",
    "schema",
    "数据库",
)
CONSTRAINT_HINTS = (
    "只",
    "仅",
    "不要",
    "保留",
    "must",
    "only",
    "without",
    "do not",
    "don't",
    "avoid",
)
NON_GOAL_HINTS = ("不要", "不需要", "无需", "不包含", "不要改", "不要动", "without", "do not")
REQUEST_SEGMENT_SPLIT_RE = re.compile(r"[\n。！？!?；;，,]+")


def derive_title(request: str, title: str | None = None) -> str:
    if title:
        return sanitize_inline(title)

    compact = sanitize_inline(request)
    if not compact:
        return "generated-demand"

    sentence = re.split(r"[。！？!?；;\n]", compact, maxsplit=1)[0].strip()
    if not sentence:
        sentence = compact
    if len(sentence) <= 48:
        return sentence
    return sentence[:48].rstrip()


def infer_task_type(text: str) -> str:
    lowered = text.lower()
    for task_type, keywords in TASK_TYPE_KEYWORDS:
        if any(keyword.lower() in lowered for keyword in keywords):
            return task_type
    return "implementation"


def infer_risk_level(text: str) -> str:
    lowered = text.lower()
    if any(keyword.lower() in lowered for keyword in HIGH_RISK_KEYWORDS):
        return "high"
    if any(keyword.lower() in lowered for keyword in MEDIUM_RISK_KEYWORDS):
        return "medium"
    return "low"


def infer_confirmation_required(text: str) -> str:
    lowered = text.lower()
    return "true" if any(keyword.lower() in lowered for keyword in CONFIRMATION_KEYWORDS) else "false"


def split_request_segments(text: str) -> list[str]:
    return [segment.strip() for segment in REQUEST_SEGMENT_SPLIT_RE.split(text) if segment.strip()]


def dedupe_preserve_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


def extract_lines_by_hints(text: str, hints: tuple[str, ...]) -> list[str]:
    matched = [
        sanitize_inline(segment)
        for segment in split_request_segments(text)
        if any(hint.lower() in segment.lower() for hint in hints)
    ]
    return dedupe_preserve_order(matched)


def infer_constraints(request: str, *, excluded: set[str] | None = None) -> list[str]:
    matched = [
        item
        for item in extract_lines_by_hints(request, CONSTRAINT_HINTS)
        if item not in (excluded or set())
    ]
    if matched:
        return matched[:3]
    return [
        "keep ACTIVE.md as the only runtime truth",
        "do not rewrite unrelated existing activities",
    ]


def infer_non_goals(request: str) -> list[str]:
    matched = extract_lines_by_hints(request, NON_GOAL_HINTS)
    if matched:
        return matched[:3]
    return [
        "do not silently modify unrelated roadmap or task files",
    ]


def infer_expected_artifacts(
    task_type: str,
    demand_doc: str,
    roadmap_doc: str,
    tasks_doc: str,
    activity_id: str,
) -> list[str]:
    primary = {
        "implementation": "implementation-ready roadmap/tasks/ACTIVE draft",
        "refactor": "refactor plan and bounded task slices",
        "governance": "governance-safe execution artifacts",
        "testing": "test-oriented execution backlog",
        "docs": "documentation-oriented execution backlog",
        "coordination": "coordination-ready execution backlog",
        "simple": "small scoped execution backlog",
    }[task_type]
    return [
        demand_doc,
        roadmap_doc,
        tasks_doc,
        f"ACTIVE activity `{activity_id}`",
        primary,
    ]


def infer_validation_plan() -> list[str]:
    return [
        DEMAND_SCHEMA_COMMAND,
        CONSISTENCY_COMMAND,
        VALIDATION_CHECKS_COMMAND,
    ]


def current_timestamp() -> str:
    now = datetime.now().astimezone()
    zone = now.tzinfo.tzname(now) if now.tzinfo else "local"
    return f"{now:%Y-%m-%d %H:%M} {zone}"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(WORKSPACE), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def ensure_paths_available(*paths: Path) -> None:
    conflicts = [
        str(path.relative_to(WORKSPACE) if path.is_absolute() and WORKSPACE in path.parents else path)
        for path in paths
        if path.exists()
    ]
    if conflicts:
        raise ValueError(f"generated paths already exist: {', '.join(conflicts)}")


def next_focus_rank(ledger) -> str:
    ranks: list[int] = []
    for activity in ledger.list_activities():
        raw = activity.scalar("focus_rank")
        if raw is None:
            continue
        try:
            ranks.append(int(raw))
        except ValueError:
            continue
    return str(max(ranks, default=0) + 1)


def slice_short_ids(count: int) -> list[str]:
    return [f"{chr(ord('A') + index)}1" for index in range(count)]


def parse_bullet_fields(lines: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    scalars: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    current_list_key: str | None = None

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        scalar_match = re.match(r"^- ([^:]+):(?: `([^`]+)`| (.+))$", stripped)
        if scalar_match:
            current_list_key = None
            key = scalar_match.group(1).strip()
            value = scalar_match.group(2) if scalar_match.group(2) is not None else scalar_match.group(3)
            scalars[key] = sanitize_inline(value or "")
            continue

        list_key_match = re.match(r"^- ([^:]+):$", stripped)
        if list_key_match:
            current_list_key = list_key_match.group(1).strip()
            lists.setdefault(current_list_key, [])
            continue

        list_item_match = re.match(r"^  - (.+)$", line)
        if current_list_key and list_item_match:
            lists.setdefault(current_list_key, []).append(sanitize_inline(list_item_match.group(1)))
            continue

        current_list_key = None

    return scalars, lists


def extract_heading_section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return []

    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def extract_flat_list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("- "):
            items.append(sanitize_inline(stripped[2:]))
    return items


def parse_contract_guardrails(contract_path: Path) -> ContractGuardrails:
    if not contract_path.exists():
        return DEFAULT_GUARDRAILS

    text = contract_path.read_text(encoding="utf-8")
    guardrail_lines = extract_heading_section(text, "## Decomposition Guardrails")
    review_lines = extract_heading_section(text, "## Review triggers")
    scalars, lists = parse_bullet_fields(guardrail_lines)

    return ContractGuardrails(
        allowed_slice_shapes=lists.get("allowed_slice_shapes", DEFAULT_GUARDRAILS.allowed_slice_shapes),
        forbidden_slice_shapes=lists.get("forbidden_slice_shapes", DEFAULT_GUARDRAILS.forbidden_slice_shapes),
        preferred_dependency_shape=scalars.get(
            "preferred_dependency_shape",
            DEFAULT_GUARDRAILS.preferred_dependency_shape,
        ),
        parallelism_policy=scalars.get("parallelism_policy", DEFAULT_GUARDRAILS.parallelism_policy),
        integration_constraints=lists.get(
            "integration_constraints",
            DEFAULT_GUARDRAILS.integration_constraints,
        ),
        review_triggers=extract_flat_list_items(review_lines) or DEFAULT_GUARDRAILS.review_triggers,
    )


def default_wave_shape(guardrails: ContractGuardrails) -> str:
    policy = guardrails.preferred_dependency_shape.lower()
    if "mixed" in policy:
        return "mixed"
    if "parallel" in policy and "serial-first" not in policy:
        return "parallel-wave"
    return "serial"


def serial_dependency_graph(full_ids: list[str]) -> list[str]:
    return [" -> ".join(full_ids)] if full_ids else []


def make_slice(
    short_id: str,
    title: str,
    phase_id: str,
    goal: list[str],
    scope: list[str],
    target_files: list[str],
    depends_on: list[str],
    expected_artifacts: list[str],
    integration_notes: list[str],
    handoff_output: list[str],
    validation: list[str],
    done_definition: list[str],
    rollback_strategy: list[str],
    risk: str,
    *,
    parallel_safe: bool = False,
    shared_write_targets: list[str] | None = None,
) -> SlicePlan:
    resolved_shared_targets = shared_write_targets if shared_write_targets is not None else list(target_files)
    return SlicePlan(
        short_id=short_id,
        title=title,
        phase_id=phase_id,
        goal=goal,
        scope=scope,
        target_files=target_files,
        depends_on=depends_on,
        parallel_safe=parallel_safe,
        shared_write_targets=resolved_shared_targets,
        expected_artifacts=expected_artifacts,
        integration_notes=integration_notes,
        handoff_output=handoff_output,
        validation=validation,
        done_definition=done_definition,
        rollback_strategy=rollback_strategy,
        risk=risk,
    )


class DemandClassifier:
    def classify(self, request: str, *, title: str | None = None) -> DemandClassification:
        normalized_request = sanitize_inline(request)
        if not normalized_request:
            raise ValueError("request must not be empty")

        resolved_title = derive_title(normalized_request, title)
        combined_text = f"{resolved_title} {normalized_request}"
        non_goals = infer_non_goals(normalized_request)
        return DemandClassification(
            title=resolved_title,
            request=normalized_request,
            task_type=infer_task_type(combined_text),
            risk_level=infer_risk_level(combined_text),
            external_confirmation_required=infer_confirmation_required(combined_text),
            constraints=infer_constraints(normalized_request, excluded=set(non_goals)),
            non_goals=non_goals,
        )


class DecompositionPlanner:
    def __init__(self, guardrails: ContractGuardrails) -> None:
        self.guardrails = guardrails

    def plan(
        self,
        classification: DemandClassification,
        *,
        today: str | None = None,
        slug: str | None = None,
    ) -> DecompositionPlan:
        slug = slugify(slug or classification.title, fallback_text=classification.request)
        date_prefix = today or datetime.now().astimezone().strftime("%Y-%m-%d")
        activity_id = f"auto-{slug}"
        project_code = build_project_code(slug)
        activity_root = f"activities/{activity_id}"
        demand_doc = f"{activity_root}/0-demand.md"
        roadmap_doc = f"{activity_root}/2-roadmap.md"
        tasks_doc = f"{activity_root}/3-tasks/{slug}-tasks.md"
        contract_doc = CONTRACT_DOC

        strategy = self.select_strategy(classification)
        manual_review_required = (
            classification.risk_level == "high"
            or classification.external_confirmation_required == "true"
        )
        phases, slices = self.build_strategy_artifacts(
            strategy,
            classification,
            project_code=project_code,
            demand_doc=demand_doc,
            roadmap_doc=roadmap_doc,
            tasks_doc=tasks_doc,
            contract_doc=contract_doc,
            manual_review_required=manual_review_required,
        )
        full_ids = [f"{project_code}.{slice_plan.short_id}" for slice_plan in slices]
        return DecompositionPlan(
            title=classification.title,
            request=classification.request,
            slug=slug,
            activity_id=activity_id,
            project_code=project_code,
            task_type=classification.task_type,
            risk_level=classification.risk_level,
            strategy=strategy,
            demand_doc=demand_doc,
            roadmap_doc=roadmap_doc,
            tasks_doc=tasks_doc,
            contract_doc=contract_doc,
            guardrails=self.guardrails,
            phases=phases,
            slices=slices,
            current_slice_id=full_ids[0],
            next_slice_id=full_ids[1],
            manual_review_required=manual_review_required,
            external_confirmation_required=classification.external_confirmation_required,
            constraints=classification.constraints,
            non_goals=classification.non_goals,
        )

    def select_strategy(self, classification: DemandClassification) -> str:
        if classification.risk_level == "high" or classification.external_confirmation_required == "true":
            return "implementation-review-gate"
        if classification.task_type in {"docs", "simple"}:
            return "light-delivery"
        if classification.task_type == "testing":
            return "testing-delivery"
        return "implementation-standard"

    def build_strategy_artifacts(
        self,
        strategy: str,
        classification: DemandClassification,
        *,
        project_code: str,
        demand_doc: str,
        roadmap_doc: str,
        tasks_doc: str,
        contract_doc: str,
        manual_review_required: bool,
    ) -> tuple[list[PhasePlan], list[SlicePlan]]:
        if strategy == "light-delivery":
            return self.build_light_delivery(
                classification,
                project_code=project_code,
                demand_doc=demand_doc,
                roadmap_doc=roadmap_doc,
                tasks_doc=tasks_doc,
            )
        if strategy == "testing-delivery":
            return self.build_testing_delivery(
                classification,
                project_code=project_code,
                demand_doc=demand_doc,
                roadmap_doc=roadmap_doc,
                tasks_doc=tasks_doc,
            )
        if strategy == "implementation-review-gate":
            return self.build_review_gate_delivery(
                classification,
                project_code=project_code,
                demand_doc=demand_doc,
                roadmap_doc=roadmap_doc,
                tasks_doc=tasks_doc,
                contract_doc=contract_doc,
            )
        return self.build_standard_delivery(
            classification,
            project_code=project_code,
            demand_doc=demand_doc,
            roadmap_doc=roadmap_doc,
            tasks_doc=tasks_doc,
            contract_doc=contract_doc,
            manual_review_required=manual_review_required,
        )

    def build_light_delivery(
        self,
        classification: DemandClassification,
        *,
        project_code: str,
        demand_doc: str,
        roadmap_doc: str,
        tasks_doc: str,
    ) -> tuple[list[PhasePlan], list[SlicePlan]]:
        short_ids = slice_short_ids(2)
        full_ids = [f"{project_code}.{short_id}" for short_id in short_ids]
        wave_shape = default_wave_shape(self.guardrails)
        phases = [
            PhasePlan(
                name="Phase 1 - Demand normalization",
                objective=["将原始请求收敛为可执行的目标、约束和首个交付边界"],
                dependencies=["source demand"],
                outputs=["normalized demand card", "activity-ready roadmap/tasks shell"],
                exit_criteria=["scope, constraints, and the first delivery slice are explicit"],
                decomposition_strategy="normalize-before-delivery",
                recommended_wave_shape=wave_shape,
                risks=["inferred delivery boundary may still need a human correction"],
            ),
            PhasePlan(
                name="Phase 2 - Delivery and handoff",
                objective=[f"为 `{classification.task_type}` 类型工作生成可执行交付切片并完成 handoff 校验"],
                dependencies=["Phase 1"],
                outputs=["delivery-ready slice", "checker-accepted handoff boundary"],
                exit_criteria=["generated backlog passes consistency and canonical checks"],
                decomposition_strategy="deliver-then-validate",
                recommended_wave_shape=wave_shape,
                risks=["small scoped work may still need a follow-up domain polish slice"],
            ),
        ]
        slices = [
            make_slice(
                short_id=short_ids[0],
                title="normalize demand and delivery boundary",
                phase_id="PH-1",
                goal=["capture request, constraints, and the first delivery boundary in generated artifacts"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[],
                expected_artifacts=["normalized demand card", "reviewable delivery boundary"],
                integration_notes=[
                    "keep runtime truth inside ACTIVE while letting demand, roadmap, and tasks hold upstream decomposition truth",
                ],
                handoff_output=["generated_paths", "activity_id"],
                validation=[DEMAND_SCHEMA_COMMAND],
                done_definition=[f"`{full_ids[0]}` leaves a reviewable baseline for downstream delivery work"],
                rollback_strategy=["remove the generated demand, roadmap, tasks, and activity together if the baseline is rejected"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[1],
                title=f"generate primary {classification.task_type} artifacts and handoff boundary",
                phase_id="PH-2",
                goal=[f"shape the primary `{classification.task_type}` backlog into a delivery-ready and handoff-safe form"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[full_ids[0]],
                expected_artifacts=["primary delivery slice", "activation-safe handoff metadata"],
                integration_notes=[
                    "validate the generated artifacts as one bounded unit before any activation attempt",
                ],
                handoff_output=["validation_commands", "activation_notes"],
                validation=[DEPENDENCY_COMMAND, PARALLEL_COMMAND, CONSISTENCY_COMMAND, VALIDATION_CHECKS_COMMAND],
                done_definition=[f"`{full_ids[1]}` makes the generated backlog safe to pick up manually"],
                rollback_strategy=["revert the generated delivery backlog together if consistency or canonical checks fail"],
                risk=classification.risk_level,
            ),
        ]
        return phases, slices

    def build_testing_delivery(
        self,
        classification: DemandClassification,
        *,
        project_code: str,
        demand_doc: str,
        roadmap_doc: str,
        tasks_doc: str,
    ) -> tuple[list[PhasePlan], list[SlicePlan]]:
        short_ids = slice_short_ids(3)
        full_ids = [f"{project_code}.{short_id}" for short_id in short_ids]
        wave_shape = default_wave_shape(self.guardrails)
        phases = [
            PhasePlan(
                name="Phase 1 - Demand normalization",
                objective=["将原始请求收敛为测试目标、约束和最小可执行范围"],
                dependencies=["source demand"],
                outputs=["normalized demand card", "testing-ready roadmap/tasks shell"],
                exit_criteria=["test boundary and validation baseline are explicit"],
                decomposition_strategy="normalize-before-test-backlog",
                recommended_wave_shape=wave_shape,
                risks=["coverage boundary may need one more domain-specific correction"],
            ),
            PhasePlan(
                name="Phase 2 - Test backlog planning",
                objective=["为测试工作生成主交付切片与依赖链"],
                dependencies=["Phase 1"],
                outputs=["primary testing slice", "validation-ready dependency chain"],
                exit_criteria=["test-oriented slices and artifacts are explicit"],
                decomposition_strategy="tests-before-handoff",
                recommended_wave_shape=wave_shape,
                risks=["generated test scope may still need a focused follow-up slice"],
            ),
            PhasePlan(
                name="Phase 3 - Validation and handoff",
                objective=["确保测试 backlog 可被 checker 接受并可安全交接"],
                dependencies=["Phase 2"],
                outputs=["checker-accepted testing backlog", "handoff-ready activity metadata"],
                exit_criteria=["consistency and canonical checks pass"],
                decomposition_strategy="validate-before-activation",
                recommended_wave_shape=wave_shape,
                risks=["activation may still wait on a human review of inferred test boundaries"],
            ),
        ]
        slices = [
            make_slice(
                short_id=short_ids[0],
                title="normalize demand and testing boundary",
                phase_id="PH-1",
                goal=["capture request, constraints, and the first testing boundary in generated artifacts"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[],
                expected_artifacts=["normalized demand card", "test-ready baseline"],
                integration_notes=["keep the generated testing backlog reviewable before widening artifact scope"],
                handoff_output=["generated_paths", "activity_id"],
                validation=[DEMAND_SCHEMA_COMMAND],
                done_definition=[f"`{full_ids[0]}` leaves a reviewable baseline for generated tests"],
                rollback_strategy=["remove generated testing artifacts together if the boundary is rejected"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[1],
                title="generate primary testing artifacts",
                phase_id="PH-2",
                goal=["shape the primary testing backlog and validation chain into executable form"],
                scope=[roadmap_doc, tasks_doc],
                target_files=[roadmap_doc, tasks_doc],
                depends_on=[full_ids[0]],
                expected_artifacts=["primary testing slice", "validation-ready dependency chain"],
                integration_notes=["keep test planning serial until the write surface is understood"],
                handoff_output=["current_slice_id", "next_slice_id"],
                validation=[DEPENDENCY_COMMAND, PARALLEL_COMMAND],
                done_definition=[f"`{full_ids[1]}` becomes a concrete next-step testing boundary"],
                rollback_strategy=["revert the generated roadmap and tasks pair together if the dependency shape is invalid"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[2],
                title="validate generated testing backlog and handoff readiness",
                phase_id="PH-3",
                goal=["verify generated artifacts can enter the canonical execution flow without drift"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[full_ids[1]],
                expected_artifacts=["checker-accepted testing backlog", "activation-safe testing metadata"],
                integration_notes=["validate cross-artifact consistency before activation or closeout"],
                handoff_output=["validation_commands", "activation_notes"],
                validation=[CONSISTENCY_COMMAND, VALIDATION_CHECKS_COMMAND],
                done_definition=[f"`{full_ids[2]}` makes the generated testing backlog safe to pick up manually"],
                rollback_strategy=["revert the generated activity and testing artifacts together if consistency or canonical checks fail"],
                risk=classification.risk_level,
            ),
        ]
        return phases, slices

    def build_standard_delivery(
        self,
        classification: DemandClassification,
        *,
        project_code: str,
        demand_doc: str,
        roadmap_doc: str,
        tasks_doc: str,
        contract_doc: str,
        manual_review_required: bool,
    ) -> tuple[list[PhasePlan], list[SlicePlan]]:
        short_ids = slice_short_ids(4)
        full_ids = [f"{project_code}.{short_id}" for short_id in short_ids]
        wave_shape = default_wave_shape(self.guardrails)
        review_risk = "human boundary correction may still be needed" if manual_review_required else "inferred scope may still need a bounded correction"
        phases = [
            PhasePlan(
                name="Phase 1 - Demand normalization",
                objective=["将原始请求收敛为可执行目标、约束和验收边界"],
                dependencies=["source demand"],
                outputs=["normalized demand card", "activity-ready roadmap/tasks shell"],
                exit_criteria=["scope, constraints, and the first slice are explicit"],
                decomposition_strategy="normalize-before-guardrails",
                recommended_wave_shape=wave_shape,
                risks=[review_risk],
            ),
            PhasePlan(
                name="Phase 2 - Guardrail planning",
                objective=["将 contract guardrails 翻译成明确的 slice 边界和 review 触发点"],
                dependencies=["Phase 1"],
                outputs=["guardrail-aligned phase plan", "reviewable slice boundary"],
                exit_criteria=["dependency shape and review triggers are explicit"],
                decomposition_strategy="guardrails-before-primary-delivery",
                recommended_wave_shape=wave_shape,
                risks=["guardrails may still require a human correction when the request is ambiguous"],
            ),
            PhasePlan(
                name="Phase 3 - Primary delivery planning",
                objective=[f"为 `{classification.task_type}` 类型工作生成主交付切片与依赖链"],
                dependencies=["Phase 2"],
                outputs=["primary delivery slice", "validation-ready dependency chain"],
                exit_criteria=["primary artifacts and validation plan are explicit"],
                decomposition_strategy="primary-delivery-after-guardrails",
                recommended_wave_shape=wave_shape,
                risks=["generated artifacts may still need a domain-specific refinement slice"],
            ),
            PhasePlan(
                name="Phase 4 - Validation and handoff",
                objective=["确保生成 backlog 可被 checker 接受并可进入后续 closeout 流程"],
                dependencies=["Phase 3"],
                outputs=["checker-accepted decomposition baseline", "handoff-ready activity metadata"],
                exit_criteria=["consistency and canonical checks pass"],
                decomposition_strategy="validate-before-activation",
                recommended_wave_shape=wave_shape,
                risks=["activation without review may still be too aggressive for follow-up high-risk refinements"],
            ),
        ]
        slices = [
            make_slice(
                short_id=short_ids[0],
                title="normalize demand and execution boundary",
                phase_id="PH-1",
                goal=["capture request, constraints, and the first execution boundary in generated artifacts"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[],
                expected_artifacts=["normalized demand card", "first executable activity draft"],
                integration_notes=[
                    "keep runtime truth inside ACTIVE while letting demand, roadmap, and tasks hold upstream decomposition truth",
                ],
                handoff_output=["generated_paths", "activity_id"],
                validation=[DEMAND_SCHEMA_COMMAND],
                done_definition=[f"`{full_ids[0]}` leaves a reviewable baseline for downstream slices"],
                rollback_strategy=["remove generated artifacts together if the decomposition baseline is rejected"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[1],
                title="translate contract guardrails into a bounded slice plan",
                phase_id="PH-2",
                goal=["align the generated backlog with contract guardrails before primary delivery is widened"],
                scope=[contract_doc, demand_doc, roadmap_doc, tasks_doc],
                target_files=[roadmap_doc, tasks_doc],
                depends_on=[full_ids[0]],
                expected_artifacts=["guardrail-aligned phase plan", "reviewable slice boundary"],
                integration_notes=["freeze the dependency shape and review triggers before shaping primary delivery artifacts"],
                handoff_output=["decomposition_strategy", "review_triggers"],
                validation=[CONSISTENCY_COMMAND],
                done_definition=[f"`{full_ids[1]}` locks the bounded slice shape before primary delivery planning"],
                rollback_strategy=["revert the generated roadmap and tasks pair together if the guardrail alignment is rejected"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[2],
                title=f"generate primary {classification.task_type} artifacts",
                phase_id="PH-3",
                goal=[f"shape the primary `{classification.task_type}` backlog and required artifacts into executable form"],
                scope=[roadmap_doc, tasks_doc],
                target_files=[roadmap_doc, tasks_doc],
                depends_on=[full_ids[1]],
                expected_artifacts=["primary delivery slice", "validation-ready dependency chain"],
                integration_notes=["keep artifact production serial until the write surface is understood"],
                handoff_output=["current_slice_id", "next_slice_id"],
                validation=[DEPENDENCY_COMMAND, PARALLEL_COMMAND],
                done_definition=[f"`{full_ids[2]}` becomes a concrete next-step boundary"],
                rollback_strategy=["revert the generated roadmap and tasks pair together if the dependency shape is invalid"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[3],
                title="validate generated backlog and handoff readiness",
                phase_id="PH-4",
                goal=["verify generated artifacts can enter the canonical execution flow without schema drift"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[full_ids[2]],
                expected_artifacts=["checker-accepted decomposition baseline", "activation-safe activity metadata"],
                integration_notes=["the generated activity must stay aligned with the canonical checks runner before activation or closeout"],
                handoff_output=["validation_commands", "activation_notes"],
                validation=[CONSISTENCY_COMMAND, VALIDATION_CHECKS_COMMAND],
                done_definition=[f"`{full_ids[3]}` makes the generated backlog safe to pick up manually"],
                rollback_strategy=["revert the generated activity and artifacts together if the canonical checks fail"],
                risk=classification.risk_level,
            ),
        ]
        return phases, slices

    def build_review_gate_delivery(
        self,
        classification: DemandClassification,
        *,
        project_code: str,
        demand_doc: str,
        roadmap_doc: str,
        tasks_doc: str,
        contract_doc: str,
    ) -> tuple[list[PhasePlan], list[SlicePlan]]:
        short_ids = slice_short_ids(5)
        full_ids = [f"{project_code}.{short_id}" for short_id in short_ids]
        wave_shape = default_wave_shape(self.guardrails)
        phases = [
            PhasePlan(
                name="Phase 1 - Demand normalization",
                objective=["将高风险请求收敛为可执行目标、约束和最小 review 边界"],
                dependencies=["source demand"],
                outputs=["normalized demand card", "activity-ready roadmap/tasks shell"],
                exit_criteria=["scope, constraints, and the first review boundary are explicit"],
                decomposition_strategy="normalize-before-review-gate",
                recommended_wave_shape=wave_shape,
                risks=["high-risk requests must not widen scope before a human review"],
            ),
            PhasePlan(
                name="Phase 2 - Review gate and activation policy",
                objective=["将 contract guardrails、review triggers 和 activation policy 固化到 backlog 中"],
                dependencies=["Phase 1"],
                outputs=["review gate notes", "activation policy"],
                exit_criteria=["manual review boundary and confirmation gate are explicit"],
                decomposition_strategy="review-gate-before-primary-delivery",
                recommended_wave_shape=wave_shape,
                risks=["activation remains blocked until explicit confirmation is recorded"],
            ),
            PhasePlan(
                name="Phase 3 - Primary delivery planning",
                objective=[f"为高风险 `{classification.task_type}` 工作生成主交付切片与依赖链"],
                dependencies=["Phase 2"],
                outputs=["primary delivery slice", "validation-ready dependency chain"],
                exit_criteria=["primary artifacts and dependency shape are explicit"],
                decomposition_strategy="primary-delivery-after-review-gate",
                recommended_wave_shape=wave_shape,
                risks=["generated artifacts must remain serial until the write surface is fully understood"],
            ),
            PhasePlan(
                name="Phase 4 - Consistency validation",
                objective=["确保 generated demand / roadmap / tasks / ACTIVE 活动卡片没有跨工件漂移"],
                dependencies=["Phase 3"],
                outputs=["checker-accepted decomposition baseline", "confirmation-safe activation boundary"],
                exit_criteria=["cross-artifact consistency and graph checks pass"],
                decomposition_strategy="cross-artifact-consistency-before-activation",
                recommended_wave_shape=wave_shape,
                risks=["activation remains blocked if any review or consistency drift remains"],
            ),
            PhasePlan(
                name="Phase 5 - Handoff readiness",
                objective=["确认该高风险 backlog 已具备 handoff-ready 的 review 与 validation 说明"],
                dependencies=["Phase 4"],
                outputs=["handoff-ready activity metadata", "manual review packet"],
                exit_criteria=["canonical checks pass and the review gate is explicit"],
                decomposition_strategy="handoff-after-explicit-review-boundary",
                recommended_wave_shape=wave_shape,
                risks=["autonomous execution must remain disabled until a human explicitly decides otherwise"],
            ),
        ]
        slices = [
            make_slice(
                short_id=short_ids[0],
                title="normalize demand and review boundary",
                phase_id="PH-1",
                goal=["capture request, constraints, and the first high-risk review boundary in generated artifacts"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[],
                expected_artifacts=["normalized demand card", "high-risk review baseline"],
                integration_notes=["keep runtime truth inside ACTIVE and keep the first wave strictly bounded"],
                handoff_output=["generated_paths", "activity_id"],
                validation=[DEMAND_SCHEMA_COMMAND],
                done_definition=[f"`{full_ids[0]}` leaves a reviewable high-risk baseline for downstream slices"],
                rollback_strategy=["remove generated artifacts together if the high-risk baseline is rejected"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[1],
                title="freeze review gate and activation policy",
                phase_id="PH-2",
                goal=["translate contract guardrails and review triggers into an explicit activation gate"],
                scope=[contract_doc, demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[full_ids[0]],
                expected_artifacts=["review gate notes", "activation policy"],
                integration_notes=["do not activate or widen scope without an explicit confirmation boundary"],
                handoff_output=["review_triggers", "activation_policy"],
                validation=[CONSISTENCY_COMMAND],
                done_definition=[f"`{full_ids[1]}` freezes the review gate before primary delivery planning"],
                rollback_strategy=["revert the generated review gate together if the activation policy is not explicit enough"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[2],
                title=f"generate primary {classification.task_type} artifacts under review guardrails",
                phase_id="PH-3",
                goal=[f"shape the high-risk `{classification.task_type}` backlog into bounded executable artifacts"],
                scope=[roadmap_doc, tasks_doc],
                target_files=[roadmap_doc, tasks_doc],
                depends_on=[full_ids[1]],
                expected_artifacts=["primary delivery slice", "validation-ready dependency chain"],
                integration_notes=["keep the first generated wave serial until the guarded write surface is understood"],
                handoff_output=["current_slice_id", "next_slice_id"],
                validation=[DEPENDENCY_COMMAND, PARALLEL_COMMAND],
                done_definition=[f"`{full_ids[2]}` becomes a guarded primary-delivery boundary"],
                rollback_strategy=["revert the generated roadmap and tasks pair together if the guarded dependency shape is invalid"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[3],
                title="validate cross-artifact consistency and activation safety",
                phase_id="PH-4",
                goal=["verify generated artifacts stay aligned before any activation or handoff"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[full_ids[2]],
                expected_artifacts=["checker-accepted decomposition baseline", "confirmation-safe activation boundary"],
                integration_notes=["run the cross-artifact consistency gate before canonical checks"],
                handoff_output=["validation_commands", "activation_guard"],
                validation=[CONSISTENCY_COMMAND, DEPENDENCY_COMMAND, PARALLEL_COMMAND],
                done_definition=[f"`{full_ids[3]}` proves the guarded backlog is internally consistent"],
                rollback_strategy=["revert the generated activity and artifacts together if any consistency gate fails"],
                risk=classification.risk_level,
            ),
            make_slice(
                short_id=short_ids[4],
                title="finalize handoff-ready review notes",
                phase_id="PH-5",
                goal=["verify the high-risk backlog can enter the canonical execution flow without hidden review drift"],
                scope=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                target_files=[demand_doc, roadmap_doc, tasks_doc, "ACTIVE.md"],
                depends_on=[full_ids[3]],
                expected_artifacts=["handoff-ready activity metadata", "manual review packet"],
                integration_notes=["keep autonomous execution disabled and preserve the review gate in ACTIVE metadata"],
                handoff_output=["activation_notes", "manual_review_packet"],
                validation=[CONSISTENCY_COMMAND, VALIDATION_CHECKS_COMMAND],
                done_definition=[f"`{full_ids[4]}` makes the guarded backlog safe to pick up manually after explicit review"],
                rollback_strategy=["revert the generated guarded backlog together if canonical checks fail"],
                risk=classification.risk_level,
            ),
        ]
        return phases, slices


class ArtifactRenderer:
    def render_demand(self, plan: DecompositionPlan) -> str:
        full_ids = [f"{plan.project_code}.{slice_plan.short_id}" for slice_plan in plan.slices]
        parallelizable_units = [full_id for full_id, slice_plan in zip(full_ids, plan.slices) if slice_plan.parallel_safe]
        card = DemandCard(
            title=plan.title,
            request=plan.request,
            task_type=plan.task_type,
            desired_outcome=f"将“{plan.title}”转成可执行、可验证、可恢复的 roadmap/tasks/ACTIVE 交付形态",
            scope=[
                "original natural-language request",
                plan.demand_doc,
                plan.roadmap_doc,
                plan.tasks_doc,
                "ACTIVE.md generated activity entry",
            ],
            constraints=plan.constraints,
            non_goals=plan.non_goals,
            risk_level=plan.risk_level,
            external_confirmation_required=plan.external_confirmation_required,
            dependency_graph=serial_dependency_graph(full_ids),
            parallelizable_units=parallelizable_units or ["none"],
            serial_units=full_ids,
            expected_artifacts=infer_expected_artifacts(
                plan.task_type,
                plan.demand_doc,
                plan.roadmap_doc,
                plan.tasks_doc,
                plan.activity_id,
            ),
            validation_plan=infer_validation_plan(),
            closeout_condition=[
                "generated demand / roadmap / tasks stay aligned",
                "generated activity passes cross-artifact consistency checks",
                "ACTIVE contains the generated activity card",
                "canonical execution checks pass",
            ],
        )
        return render_demand_card(card)

    def render_roadmap(self, plan: DecompositionPlan) -> str:
        lines = [
            f"# {sanitize_inline(plan.title)} roadmap",
            "",
            "## Goal",
            f"- 将需求 `{sanitize_inline(plan.title)}` 从自然语言请求收敛成可执行 backlog，并保持 execution-system 约束不漂移。",
            "",
            "## Contract reference",
            f"- `{plan.contract_doc}`",
            "",
            "## Source demand",
            f"- `{plan.demand_doc}`",
            "",
            "## Validation baseline",
            f"- `{DEMAND_SCHEMA_COMMAND}`",
            f"- `{CONSISTENCY_COMMAND}`",
            f"- `{VALIDATION_CHECKS_COMMAND}`",
            "",
            "## Phases",
            "",
        ]
        for phase in plan.phases:
            lines.append(f"### {phase.name}")
            lines.append("- objective:")
            for value in phase.objective:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- dependencies:")
            for value in phase.dependencies:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- outputs:")
            for value in phase.outputs:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- exit criteria:")
            for value in phase.exit_criteria:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- decomposition_strategy:")
            lines.append(f"  - {sanitize_inline(phase.decomposition_strategy)}")
            lines.append("- recommended_wave_shape:")
            lines.append(f"  - `{phase.recommended_wave_shape}`")
            lines.append("- risks:")
            for value in phase.risks:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("")
        lines.extend(
            [
                "## Current recommended phase",
                f"- {plan.phases[0].name} (`{plan.current_slice_id}` first)",
                "",
                "## Activity anchor",
                f"- `{plan.activity_id}`",
                "",
            ]
        )
        return "\n".join(lines)

    def render_tasks(self, plan: DecompositionPlan) -> str:
        lines = [
            f"# {sanitize_inline(plan.title)} tasks",
            "",
            "## Source demand",
            f"- `{plan.demand_doc}`",
            "",
            "## Current phase",
            f"- {plan.phases[0].name} (`{plan.project_code}` / Slice {plan.slices[0].short_id} - {sanitize_inline(plan.slices[0].title)})",
            "",
            "## PR queue",
            "",
            f"### {plan.project_code} - automated demand decomposition",
            "- goal:",
            f"  - 将 `{sanitize_inline(plan.title)}` 自动拆成可执行、可验证的 execution-system backlog",
            "- validation:",
            "  - generated demand card is schema-valid",
            "  - generated artifacts satisfy dependency, parallel-safety, and consistency checks",
            "- done_definition:",
            "  - roadmap/tasks/ACTIVE stay aligned and the next slice is explicit",
            "- risk:",
            f"  - {plan.risk_level}",
            "",
        ]
        for slice_plan in plan.slices:
            lines.append(f"#### Slice {slice_plan.short_id} - {sanitize_inline(slice_plan.title)}")
            lines.append(f"- phase_id: `{slice_plan.phase_id}`")
            lines.append("- goal:")
            for value in slice_plan.goal:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- scope:")
            for value in slice_plan.scope:
                lines.append(f"  - `{value}`" if value.endswith(".md") else f"  - {sanitize_inline(value)}")
            lines.append("- target_files:")
            for value in slice_plan.target_files:
                lines.append(f"  - `{value}`" if value.endswith(".md") else f"  - {sanitize_inline(value)}")
            lines.append("- depends_on:")
            depends = slice_plan.depends_on or ["none"]
            for value in depends:
                lines.append(f"  - `{value}`" if value != "none" else "  - none")
            lines.append("- parallel_safe:")
            lines.append(f"  - {'true' if slice_plan.parallel_safe else 'false'}")
            lines.append("- shared_write_targets:")
            shared_targets = slice_plan.shared_write_targets or ["none"]
            for value in shared_targets:
                lines.append(f"  - `{value}`" if value.endswith(".md") else f"  - {sanitize_inline(value)}")
            lines.append("- expected_artifacts:")
            for value in slice_plan.expected_artifacts:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- integration_notes:")
            for value in slice_plan.integration_notes:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- handoff_output:")
            for value in slice_plan.handoff_output:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- validation:")
            for value in slice_plan.validation:
                lines.append(f"  - `{value}`")
            lines.append("- done_definition:")
            for value in slice_plan.done_definition:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- rollback_strategy:")
            for value in slice_plan.rollback_strategy:
                lines.append(f"  - {sanitize_inline(value)}")
            lines.append("- risk:")
            lines.append(f"  - {slice_plan.risk}")
            lines.append("")
        return "\n".join(lines)

    def build_activity(
        self,
        plan: DecompositionPlan,
        *,
        last_commit: str,
        focus_rank: str,
        review_confirmed: bool,
    ) -> Activity:
        if plan.manual_review_required and not review_confirmed:
            status = "blocked"
            blocker = (
                ACTIVATION_CONFIRMATION_REASON
                if plan.external_confirmation_required == "true"
                else MANUAL_REVIEW_REASON
            )
            blocked_by = [blocker]
            next_step = [
                f"review the generated demand intake `{plan.demand_doc}`",
                f"confirm the guarded activity `{plan.activity_id}` before switching focus or enabling autonomous execution",
            ]
        else:
            status = "ready"
            blocked_by = ["none"]
            next_step = [
                f"review the generated demand intake `{plan.demand_doc}`",
                f"start `{plan.current_slice_id}` if the inferred boundary looks correct",
            ]

        autopilot = "false" if plan.manual_review_required else "true"
        done_when = [
            "generated demand / roadmap / tasks artifacts stay aligned",
            "generated tasks pass dependency and parallel-safety checks",
            "generated activity passes cross-artifact consistency checks",
            "the generated activity is safe to activate or continue manually",
        ]
        retrieval_keys = [
            plan.activity_id,
            plan.demand_doc,
            plan.roadmap_doc,
            plan.tasks_doc,
            plan.task_type,
            plan.strategy,
        ]

        fields = OrderedDict(
            (
                ("activity_id", plan.activity_id),
                ("title", f"auto decompose {sanitize_inline(plan.title)}"),
                ("type", "roadmap"),
                ("owner", "Codex"),
                ("status", status),
                ("priority", {"high": "P1", "medium": "P2", "low": "P3"}[plan.risk_level]),
                ("autopilot", autopilot),
                ("focus_rank", focus_rank),
                ("repo", WORKSPACE.name),
                ("path", "."),
                ("source_doc", plan.demand_doc),
                ("roadmap_doc", plan.roadmap_doc),
                ("tasks_doc", plan.tasks_doc),
                ("current_slice_id", plan.current_slice_id),
                ("next_slice_id", plan.next_slice_id),
                (
                    "objective",
                    f"将自然语言需求“{sanitize_inline(plan.title)}”自动拆成可执行 backlog，并保持 execution-system 约束不漂移",
                ),
                ("last_commit", last_commit),
            )
        )
        list_fields = OrderedDict(
            (
                ("done_when", done_when),
                ("next_step", next_step),
                (
                    "validation",
                    [
                        DEMAND_SCHEMA_COMMAND,
                        CONSISTENCY_COMMAND,
                        VALIDATION_CHECKS_COMMAND,
                    ],
                ),
                ("blocked_by", blocked_by),
                ("retrieval_keys", retrieval_keys),
            )
        )
        activity = Activity(plan.activity_id, dict(fields), dict(list_fields))
        activity._raw_lines = activity.to_lines()
        return activity


class ArtifactApplier:
    def apply(
        self,
        plan: DecompositionPlan,
        *,
        activate: bool = False,
        confirm: bool = False,
    ) -> DecompositionResult:
        demand_path = WORKSPACE / plan.demand_doc
        roadmap_path = WORKSPACE / plan.roadmap_doc
        tasks_path = WORKSPACE / plan.tasks_doc

        ledger = parse_ledger(ACTIVE_PATH)
        if ledger.get_activity(plan.activity_id) is not None:
            raise ValueError(f"activity `{plan.activity_id}` already exists")

        ensure_paths_available(demand_path, roadmap_path, tasks_path)
        last_commit = git_head()
        review_confirmed = confirm if plan.manual_review_required else False
        renderer = ArtifactRenderer()
        activity = renderer.build_activity(
            plan,
            last_commit=last_commit,
            focus_rank=next_focus_rank(ledger),
            review_confirmed=review_confirmed,
        )

        activation_allowed = activate and (not plan.manual_review_required or confirm)
        activation_blocked_reason = None
        if activate and not activation_allowed:
            activation_blocked_reason = MANUAL_REVIEW_OR_CONFIRM_REASON

        demand_path.parent.mkdir(parents=True, exist_ok=True)
        roadmap_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.parent.mkdir(parents=True, exist_ok=True)

        created_paths: list[Path] = []
        try:
            demand_path.write_text(renderer.render_demand(plan), encoding="utf-8")
            created_paths.append(demand_path)
            roadmap_path.write_text(renderer.render_roadmap(plan), encoding="utf-8")
            created_paths.append(roadmap_path)
            tasks_path.write_text(renderer.render_tasks(plan), encoding="utf-8")
            created_paths.append(tasks_path)

            ledger.add_activity(activity)
            meta_updates = {"updated_at": current_timestamp()}
            if activation_allowed:
                meta_updates["current_focus_activity_id"] = plan.activity_id
                meta_updates["default_reply_activity_id"] = plan.activity_id
            ledger.update_fields(**meta_updates)
            ledger.save()
        except Exception:
            for path in reversed(created_paths):
                if path.exists():
                    path.unlink()
            raise

        return DecompositionResult(
            title=plan.title,
            task_type=plan.task_type,
            risk_level=plan.risk_level,
            strategy=plan.strategy,
            activity_id=plan.activity_id,
            demand_doc=plan.demand_doc,
            roadmap_doc=plan.roadmap_doc,
            tasks_doc=plan.tasks_doc,
            current_slice_id=plan.current_slice_id,
            next_slice_id=plan.next_slice_id,
            status=activity.scalar("status") or "ready",
            autopilot=activity.scalar("autopilot") == "true",
            activated=activation_allowed,
            confirmation_required_for_activation=plan.manual_review_required,
            activation_blocked_reason=activation_blocked_reason,
        )


def plan_request(
    request: str,
    *,
    title: str | None = None,
    slug: str | None = None,
) -> DecompositionPlan:
    classification = DemandClassifier().classify(request, title=title)
    guardrails = parse_contract_guardrails(WORKSPACE / CONTRACT_DOC)
    planner = DecompositionPlanner(guardrails)
    return planner.plan(classification, slug=slug)


def decompose_request(
    request: str,
    *,
    title: str | None = None,
    slug: str | None = None,
    activate: bool = False,
    confirm: bool = False,
) -> DecompositionResult:
    plan = plan_request(request, title=title, slug=slug)
    return ArtifactApplier().apply(plan, activate=activate, confirm=confirm)
