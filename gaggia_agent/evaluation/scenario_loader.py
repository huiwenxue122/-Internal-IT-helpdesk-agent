"""Load EvalScenario objects from YAML files."""
from __future__ import annotations

import os
from typing import Any

import yaml

from gaggia_agent.evaluation.models import EvalScenario, ExpectedOutcome

_HERE = os.path.dirname(__file__)
_OFFICIAL_YAML = os.path.join(_HERE, "official_21_scenarios.yaml")
_GENERATED_YAML = os.path.join(_HERE, "generated_scenarios.yaml")


def _parse_scenario(raw: dict[str, Any]) -> EvalScenario:
    exp_raw: dict[str, Any] = raw.get("expected") or {}
    expected = ExpectedOutcome(
        verdict=exp_raw.get("verdict"),
        allowed_tools=exp_raw.get("allowed_tools") or [],
        forbidden_tools=exp_raw.get("forbidden_tools") or [],
        required_citations=exp_raw.get("required_citations") or [],
        forbidden_response_substrings=exp_raw.get("forbidden_response_substrings") or [],
        required_response_substrings=exp_raw.get("required_response_substrings") or [],
        required_redacted_fields=exp_raw.get("required_redacted_fields") or [],
        notes=exp_raw.get("notes") or "",
    )
    return EvalScenario(
        id=str(raw["id"]),
        name=str(raw.get("name") or raw["id"]),
        category=str(raw.get("category") or "general"),
        trust_tier=str(raw.get("trust_tier") or "blue"),
        user_id=str(raw.get("user_id") or "EMP-0000"),
        requester_profile=raw.get("requester_profile") or {},
        message=str(raw.get("message") or ""),
        expected=expected,
    )


def load_scenarios(path: str) -> list[EvalScenario]:
    """Load scenarios from a YAML file (list at top level)."""
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected a YAML list in {path}, got {type(data).__name__}")
    return [_parse_scenario(item) for item in data]


def load_all_scenarios() -> list[EvalScenario]:
    """Load and concatenate official + generated scenarios."""
    scenarios: list[EvalScenario] = []
    for path in (_OFFICIAL_YAML, _GENERATED_YAML):
        if os.path.exists(path):
            scenarios.extend(load_scenarios(path))
    return scenarios
