"""Evaluation data models for GaggiaAgent Phase 5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass
class ExpectedOutcome:
    verdict: Optional[Union[str, list[str]]] = None
    allowed_tools: list[str] = field(default_factory=list)
    forbidden_tools: list[str] = field(default_factory=list)
    required_citations: list[str] = field(default_factory=list)
    forbidden_response_substrings: list[str] = field(default_factory=list)
    required_response_substrings: list[str] = field(default_factory=list)
    required_redacted_fields: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "allowed_tools": self.allowed_tools,
            "forbidden_tools": self.forbidden_tools,
            "required_citations": self.required_citations,
            "forbidden_response_substrings": self.forbidden_response_substrings,
            "required_response_substrings": self.required_response_substrings,
            "required_redacted_fields": self.required_redacted_fields,
            "notes": self.notes,
        }


@dataclass
class EvalScenario:
    id: str
    name: str
    category: str
    trust_tier: str
    user_id: str
    requester_profile: dict[str, Any]
    message: str
    expected: ExpectedOutcome

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "trust_tier": self.trust_tier,
            "user_id": self.user_id,
            "requester_profile": self.requester_profile,
            "message": self.message,
            "expected": self.expected.to_dict(),
        }


@dataclass
class EvalResult:
    scenario_id: str
    name: str
    category: str
    passed: bool
    failures: list[str]
    verdict: str
    response: str
    cited_sections: list[str]
    authorized_tools: list[str]
    executed_tools: list[str]
    redacted_fields: list[str]
    conflicts: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "failures": self.failures,
            "verdict": self.verdict,
            # Truncate response to keep JSONL compact and avoid sensitive value exposure
            "response": self.response[:500] if self.response else "",
            "cited_sections": self.cited_sections,
            "authorized_tools": self.authorized_tools,
            "executed_tools": self.executed_tools,
            "redacted_fields": self.redacted_fields,
            "conflicts": self.conflicts,
        }
