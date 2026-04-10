#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

ALLOWED_TASK_TYPES = (
    "implementation",
    "refactor",
    "governance",
    "testing",
    "docs",
    "coordination",
    "simple",
)
ALLOWED_RISK_LEVELS = ("low", "medium", "high")
REQUIRED_SCALAR_FIELDS = (
    "request",
    "task_type",
    "desired_outcome",
    "risk_level",
    "external_confirmation_required",
)
REQUIRED_LIST_FIELDS = (
    "scope",
    "constraints",
    "non_goals",
    "dependency_graph",
    "parallelizable_units",
    "serial_units",
    "expected_artifacts",
    "validation_plan",
    "closeout_condition",
)


@dataclass
class DemandCard:
    title: str
    request: str
    task_type: str
    desired_outcome: str
    scope: list[str]
    constraints: list[str]
    non_goals: list[str]
    risk_level: str
    external_confirmation_required: str
    dependency_graph: list[str]
    parallelizable_units: list[str]
    serial_units: list[str]
    expected_artifacts: list[str]
    validation_plan: list[str]
    closeout_condition: list[str]


def sanitize_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "'")).strip()


def _slugify_candidate(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def slugify(text: str, fallback_text: str | None = None) -> str:
    for candidate in (text, fallback_text):
        if not candidate:
            continue
        normalized = _slugify_candidate(candidate)
        if normalized:
            return normalized[:60]

    digest_source = fallback_text or text
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:8]
    return f"request-{digest}"


def build_project_code(slug: str) -> str:
    tokens = [token for token in slug.upper().split("-") if token and token != "REQUEST"]
    letters = "".join(token[0] for token in tokens[:2])
    if len(letters) < 2:
        compact = re.sub(r"[^A-Z0-9]", "", slug.upper())
        letters = (letters + compact)[:2]
    letters = letters.ljust(2, "X")
    return f"{letters}-A"


def parse_markdown_fields(text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    fields: dict[str, str] = {}
    list_fields: dict[str, list[str]] = {}
    current_list_key: str | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        scalar_match = re.match(r"^- ([^:]+):(?: `([^`]+)`| (.+))$", stripped)
        if scalar_match:
            current_list_key = None
            key = scalar_match.group(1).strip()
            value = scalar_match.group(2) if scalar_match.group(2) is not None else scalar_match.group(3)
            fields[key] = sanitize_inline(value or "")
            continue

        list_key_match = re.match(r"^- ([^:]+):$", stripped)
        if list_key_match:
            current_list_key = list_key_match.group(1).strip()
            list_fields.setdefault(current_list_key, [])
            continue

        list_item_match = re.match(r"^  - (.+)$", line)
        if current_list_key and list_item_match:
            list_fields.setdefault(current_list_key, []).append(sanitize_inline(list_item_match.group(1)))
            continue

        current_list_key = None

    return fields, list_fields


def validate_demand_card_text(text: str, source: str) -> list[str]:
    problems: list[str] = []
    fields, list_fields = parse_markdown_fields(text)

    for key in REQUIRED_SCALAR_FIELDS:
        if not fields.get(key):
            problems.append(f"{source}: missing `{key}`")

    for key in REQUIRED_LIST_FIELDS:
        if not list_fields.get(key):
            problems.append(f"{source}: missing list `{key}`")

    task_type = fields.get("task_type", "")
    if task_type and task_type not in ALLOWED_TASK_TYPES:
        problems.append(f"{source}: invalid `task_type` `{task_type}`")

    risk_level = fields.get("risk_level", "")
    if risk_level and risk_level not in ALLOWED_RISK_LEVELS:
        problems.append(f"{source}: invalid `risk_level` `{risk_level}`")

    external_confirmation_required = fields.get("external_confirmation_required", "")
    if external_confirmation_required and external_confirmation_required not in {"true", "false"}:
        problems.append(
            f"{source}: invalid `external_confirmation_required` `{external_confirmation_required}`"
        )

    return problems


def render_demand_card(card: DemandCard) -> str:
    lines = [f"# {sanitize_inline(card.title)} demand intake", ""]
    lines.append(f"- request: {sanitize_inline(card.request)}")
    lines.append(f"- task_type: `{card.task_type}`")
    lines.append(f"- desired_outcome: {sanitize_inline(card.desired_outcome)}")
    for key, values in (
        ("scope", card.scope),
        ("constraints", card.constraints),
        ("non_goals", card.non_goals),
    ):
        lines.append(f"- {key}:")
        for value in values:
            lines.append(f"  - {sanitize_inline(value)}")
    lines.append(f"- risk_level: `{card.risk_level}`")
    lines.append(
        f"- external_confirmation_required: `{card.external_confirmation_required}`"
    )
    for key, values in (
        ("dependency_graph", card.dependency_graph),
        ("parallelizable_units", card.parallelizable_units),
        ("serial_units", card.serial_units),
        ("expected_artifacts", card.expected_artifacts),
        ("validation_plan", card.validation_plan),
        ("closeout_condition", card.closeout_condition),
    ):
        lines.append(f"- {key}:")
        for value in values:
            lines.append(f"  - {sanitize_inline(value)}")
    return "\n".join(lines) + "\n"
