"""Pydantic schemas for the GaggiaAgent demo API."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class RunAgentRequest(BaseModel):
    message: str
    trust_tier: str = "blue"
    user_id: str = "EMP-2200"
    requester_profile: Optional[dict[str, Any]] = None
    conversation_id: Optional[str] = None


class ScenarioItem(BaseModel):
    """
    Message-only template.

    suggested_* fields are display hints shown in the UI. They are NEVER
    automatically applied to the actual request — the user must explicitly
    click "Apply suggested context" to opt in. The backend ignores them
    entirely; it uses only the values in RunAgentRequest.
    """
    id: str
    name: str
    description: str
    message: str
    category: str                               # clearly_allowed | clearly_denied | ambiguous | adversarial
    suggested_trust_tier: Optional[str] = None
    suggested_user_id: Optional[str] = None
    suggested_profile_id: Optional[str] = None


class SubmittedInput(BaseModel):
    trust_tier: str
    user_id: str
    message: str
    requester_profile: Optional[dict[str, Any]] = None


class AgentResponse(BaseModel):
    # Echoes exactly what was submitted so the UI can verify tier/profile
    submitted_input: SubmittedInput
    # Agent outputs
    response: str
    verdict: str
    cited_sections: list[str]
    intent: str
    requested_fields: list[str]
    candidate_tools: list[str]
    risk_level: str
    adversarial_signals: list[str]
    retrieved_sections: list[dict[str, Any]]
    retrieved_rules: list[dict[str, Any]]
    graph_expanded_rules: list[dict[str, Any]]
    conflicts_detected: list[dict[str, Any]]
    allowed_tool_calls: list[dict[str, Any]]
    authorized_tool_calls: list[dict[str, Any]]
    blocked_by_guard: list[dict[str, Any]]
    executed_tools: list[str]
    filtered_tool_outputs: dict[str, Any]
    redacted_fields: list[str]
    retrieval_metadata: dict[str, Any]
    decision_log_summary: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    service: str
    llm_mode: str
    version: str
