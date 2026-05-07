"""
gaggia_agent/graph.py

Assembles the full GaggiaAgent workflow as a LangGraph StateGraph.

Node execution order:

  router_agent
    -> trust_tier_guard
    -> policy_retriever
    -> conflict_detector
    -> policy_reasoning_agent
    -> [conditional branch on verdict]
         allow    -> tool_authorization_guard -> tool_executor -> output_filter
         escalate -> ensure_escalation_tool_call -> tool_authorization_guard -> tool_executor -> output_filter
         deny     ─────────────────────────────────────────────────────────────────────────────────────────┐
         clarify  ─────────────────────────────────────────────────────────────────────────────────────────┤
                                                                                                           ↓
                                                                                               response_agent
                                                                                               -> decision_logger
                                                                                               -> END

Architectural invariants enforced by the graph:
 - LLM agents never appear in the tool-execution path.
 - All tool calls must pass through tool_authorization_guard.
 - Output filtering always precedes response generation for tool-bearing paths.
 - Decision logging always runs last.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from gaggia_agent.agents.policy_reasoning_agent import policy_reasoning_agent
from gaggia_agent.agents.response_agent import response_agent
from gaggia_agent.agents.router_agent import router_agent
from gaggia_agent.nodes.conflict_detector import conflict_detector
from gaggia_agent.nodes.decision_logger import decision_logger
from gaggia_agent.nodes.output_filter import output_filter
from gaggia_agent.nodes.policy_retriever import policy_retriever
from gaggia_agent.nodes.tool_authorization_guard import tool_authorization_guard
from gaggia_agent.nodes.tool_executor import tool_executor
from gaggia_agent.nodes.trust_tier_guard import trust_tier_guard
from gaggia_agent.state import AgentState

# ---------------------------------------------------------------------------
# Utility node: ensure escalation tool call exists when verdict == "escalate"
# ---------------------------------------------------------------------------

def ensure_escalation_tool_call(state: AgentState) -> AgentState:
    """
    If verdict == 'escalate' but no escalate_to_human call is in
    allowed_tool_calls, synthesize one so the tool-execution path can
    create a human-review ticket.

    Idempotent: if a valid escalation call already exists, state is unchanged.
    """
    if state.get("verdict") != "escalate":
        return state

    allowed = state.get("allowed_tool_calls") or []
    if any(c.get("tool") == "escalate_to_human" for c in allowed):
        return state

    synthesized_call = {
        "tool": "escalate_to_human",
        "args": {
            "reason": state.get("reasoning_summary") or "Request requires human review",
            "conversation_summary": state.get("user_message", ""),
        },
        "reason": "Escalation verdict requires human review ticket",
    }
    return {**state, "allowed_tool_calls": [synthesized_call]}


# ---------------------------------------------------------------------------
# Routing function: branch after policy_reasoning_agent
# ---------------------------------------------------------------------------

_VALID_VERDICTS = {"allow", "deny", "clarify", "escalate"}


def route_after_policy_decision(state: AgentState) -> str:
    """
    Return the graph branch to follow based on the policy verdict.

    Any unrecognised verdict is treated as 'deny' to fail safely.
    """
    verdict = state.get("verdict", "")
    if verdict in _VALID_VERDICTS:
        return verdict
    return "deny"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

_compiled_graph = None


def build_graph():
    """
    Build and compile the GaggiaAgent LangGraph StateGraph.

    Returns a compiled graph that can be invoked with an AgentState dict.
    """
    workflow: StateGraph = StateGraph(AgentState)

    # ---- Register nodes ----
    workflow.add_node("router_agent", router_agent)
    workflow.add_node("trust_tier_guard", trust_tier_guard)
    workflow.add_node("policy_retriever", policy_retriever)
    workflow.add_node("conflict_detector", conflict_detector)
    workflow.add_node("policy_reasoning_agent", policy_reasoning_agent)
    workflow.add_node("ensure_escalation_tool_call", ensure_escalation_tool_call)
    workflow.add_node("tool_authorization_guard", tool_authorization_guard)
    workflow.add_node("tool_executor", tool_executor)
    workflow.add_node("output_filter", output_filter)
    workflow.add_node("response_agent", response_agent)
    workflow.add_node("decision_logger", decision_logger)

    # ---- Linear pre-decision edges ----
    workflow.set_entry_point("router_agent")
    workflow.add_edge("router_agent", "trust_tier_guard")
    workflow.add_edge("trust_tier_guard", "policy_retriever")
    workflow.add_edge("policy_retriever", "conflict_detector")
    workflow.add_edge("conflict_detector", "policy_reasoning_agent")

    # ---- Conditional routing after policy decision ----
    workflow.add_conditional_edges(
        "policy_reasoning_agent",
        route_after_policy_decision,
        {
            "allow": "tool_authorization_guard",
            "escalate": "ensure_escalation_tool_call",
            "deny": "response_agent",
            "clarify": "response_agent",
        },
    )

    # ---- Escalation path ----
    workflow.add_edge("ensure_escalation_tool_call", "tool_authorization_guard")

    # ---- Tool execution path (allow and escalate converge here) ----
    workflow.add_edge("tool_authorization_guard", "tool_executor")
    workflow.add_edge("tool_executor", "output_filter")
    workflow.add_edge("output_filter", "response_agent")

    # ---- Final path (all verdicts converge at response_agent) ----
    workflow.add_edge("response_agent", "decision_logger")
    workflow.add_edge("decision_logger", END)

    return workflow.compile()


def get_compiled_graph():
    """Return a cached compiled graph (built once per process)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
