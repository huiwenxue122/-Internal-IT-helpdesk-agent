"""
gaggia_agent/runner.py

High-level entry point for running the full GaggiaAgent pipeline.
Wraps the compiled LangGraph with convenient Python-callable functions.

LangSmith tracing
-----------------
Set these environment variables (or copy .env.example → .env and fill in):

    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=<your key from https://smith.langchain.com>
    LANGCHAIN_PROJECT=gaggia-agent   # optional, defaults to "default"

When tracing is active every run_agent() call creates a trace in LangSmith
with the full node-by-node execution, input/output at each step, and timing.
"""

from __future__ import annotations

import os
from typing import Any

# Load .env at project root so LANGCHAIN_* and ANTHROPIC_API_KEY are available
# before any LangChain/LangSmith imports. This is a no-op if .env doesn't exist.
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(override=False)  # override=False: existing shell env vars win
except ImportError:
    pass

from gaggia_agent.state import AgentState, default_state

# Apply compatibility patch before any langgraph / langchain-core import.
# See gaggia_agent/_compat.py for full explanation.
import gaggia_agent._compat  # noqa: F401

_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        from gaggia_agent.graph import build_graph
        _compiled_graph = build_graph()
    return _compiled_graph


def _tracing_active() -> bool:
    """Return True when LangSmith tracing env vars are configured."""
    return (
        os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"
        and bool(os.environ.get("LANGCHAIN_API_KEY", "").strip())
    )


def run_agent(
    user_message: str,
    user_id: str,
    trust_tier: str,
    requester_profile: dict[str, Any] | None = None,
    conversation_id: str | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
) -> AgentState:
    """
    Run the full GaggiaAgent pipeline for a single user request.

    Parameters
    ----------
    user_message:
        The user's free-text helpdesk request.
    user_id:
        The requester's employee ID or system identifier.
    trust_tier:
        "blue" (verified employee), "grey" (contractor / vendor), or
        "red" (untrusted / external).
    requester_profile:
        Optional dict with additional context (e.g. is_manager, reports).
    conversation_id:
        Optional conversation / session identifier for logging.
    conversation_history:
        Optional prior turns in this conversation.

    Returns
    -------
    AgentState:
        The final state after the full graph execution, including response,
        verdict, cited_sections, tool outputs (filtered), and decision log.
    """
    conv_id = conversation_id or "CONV-LOCAL-001"
    initial_state = default_state(
        user_message=user_message,
        user_id=user_id,
        trust_tier=trust_tier,
        requester_profile=requester_profile,
        conversation_id=conv_id,
        conversation_history=conversation_history,
    )
    graph = _get_graph()

    # Build LangSmith-friendly invoke config.
    # run_name  → shows up as the trace title in the LangSmith UI.
    # metadata  → searchable key/value pairs on each run.
    # tags      → filterable labels (trust tier, project phase).
    # These fields are ignored silently when tracing is disabled.
    run_name = f"gaggia-agent | {trust_tier} | {user_id}"
    invoke_config: dict[str, Any] = {
        "run_name": run_name,
        "metadata": {
            "user_id": user_id,
            "trust_tier": trust_tier,
            "conversation_id": conv_id,
            # Truncate message so it's readable in the UI without leaking sensitive text.
            "user_message_preview": user_message[:120],
        },
        "tags": [
            "gaggia-agent",
            f"tier:{trust_tier}",
        ],
    }

    final_state: AgentState = graph.invoke(initial_state, config=invoke_config)
    return final_state


def summarize_final_state(state: AgentState) -> dict[str, Any]:
    """
    Return a compact summary dict suitable for CLI display and testing.

    Does NOT include raw_tool_outputs (privacy-preserving).
    """
    return {
        "response": state.get("response", ""),
        "verdict": state.get("verdict", ""),
        "cited_sections": state.get("cited_sections", []),
        "intent": state.get("intent", ""),
        "requested_fields": state.get("requested_fields", []),
        "candidate_tools": state.get("candidate_tools", []),
        "retrieved_rule_ids": [
            r.get("rule_id", "") for r in (state.get("retrieved_rules") or [])
        ],
        "conflicts": state.get("conflicts_detected", []),
        "authorized_tool_calls": state.get("authorized_tool_calls", []),
        "blocked_by_guard": state.get("blocked_by_guard", []),
        "redacted_fields": state.get("redacted_fields", []),
        "retrieval_metadata": state.get("retrieval_metadata", {}),
    }
