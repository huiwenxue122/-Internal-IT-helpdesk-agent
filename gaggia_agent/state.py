from __future__ import annotations

from typing import List, Dict, Any

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Input
    user_message: str
    user_id: str
    trust_tier: str  # "blue" | "grey" | "red"
    requester_profile: Dict[str, Any]
    conversation_id: str
    conversation_history: List[Dict[str, Any]]

    # Router output
    intent: str
    target_entities: List[Dict[str, Any]]
    requested_fields: List[str]
    candidate_tools: List[str]
    risk_level: str  # "low" | "medium" | "high"
    adversarial_signals: List[str]

    # Trust constraints
    trust_constraints: List[str]
    allowed_tools_by_trust: List[str]

    # Policy retrieval
    retrieved_sections: List[Dict[str, Any]]
    retrieved_rules: List[Dict[str, Any]]
    graph_expanded_rules: List[Dict[str, Any]]
    conflicts_detected: List[Dict[str, Any]]

    # Policy decision
    verdict: str  # "allow" | "deny" | "clarify" | "escalate"
    cited_sections: List[str]
    reasoning_summary: str
    allowed_tool_calls: List[Dict[str, Any]]
    blocked_tool_calls: List[Dict[str, Any]]
    output_constraints: Dict[str, Any]

    # Execution
    authorized_tool_calls: List[Dict[str, Any]]
    blocked_by_guard: List[Dict[str, Any]]
    raw_tool_outputs: Dict[str, Any]
    filtered_tool_outputs: Dict[str, Any]
    redacted_fields: List[str]

    # Retrieval observability
    retrieval_metadata: Dict[str, Any]

    # Final
    response: str
    decision_log: Dict[str, Any]


def default_state(
    user_message: str,
    user_id: str,
    trust_tier: str,
    requester_profile: Dict[str, Any] | None = None,
    conversation_id: str = "CONV-LOCAL-001",
    conversation_history: List[Dict[str, Any]] | None = None,
) -> AgentState:
    return AgentState(
        # Input
        user_message=user_message,
        user_id=user_id,
        trust_tier=trust_tier,
        requester_profile=requester_profile if requester_profile is not None else {},
        conversation_id=conversation_id,
        conversation_history=conversation_history if conversation_history is not None else [],

        # Router output
        intent="",
        target_entities=[],
        requested_fields=[],
        candidate_tools=[],
        risk_level="",
        adversarial_signals=[],

        # Trust constraints
        trust_constraints=[],
        allowed_tools_by_trust=[],

        # Policy retrieval
        retrieved_sections=[],
        retrieved_rules=[],
        graph_expanded_rules=[],
        conflicts_detected=[],
        retrieval_metadata={},

        # Policy decision
        verdict="",
        cited_sections=[],
        reasoning_summary="",
        allowed_tool_calls=[],
        blocked_tool_calls=[],
        output_constraints={},

        # Execution
        authorized_tool_calls=[],
        blocked_by_guard=[],
        raw_tool_outputs={},
        filtered_tool_outputs={},
        redacted_fields=[],

        # Final
        response="",
        decision_log={},
    )
