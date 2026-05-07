from __future__ import annotations

import json
import os
import random
import string
from datetime import datetime, timezone

from gaggia_agent.state import AgentState

_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "decisions.jsonl")


def decision_logger(state: AgentState) -> AgentState:
    log_dir = os.path.dirname(os.path.abspath(_LOG_PATH))
    os.makedirs(log_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y%m%d%H%M%S")
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    trace_id = f"REQ-{timestamp_str}-{random_suffix}"

    log_entry: dict = {
        "trace_id": trace_id,
        "conversation_id": state.get("conversation_id", ""),
        "timestamp": now.isoformat(),
        "input": {
            "trust_tier": state.get("trust_tier", ""),
            "user_id": state.get("user_id", ""),
            "message": state.get("user_message", ""),
        },
        "router": {
            "intent": state.get("intent", ""),
            "requested_fields": state.get("requested_fields", []),
            "candidate_tools": state.get("candidate_tools", []),
            "risk_level": state.get("risk_level", ""),
            "adversarial_signals": state.get("adversarial_signals", []),
        },
        "policy_retrieval": {
            "sections": state.get("retrieved_sections", []),
            "rules": state.get("retrieved_rules", []),
            "graph_expanded_rules": state.get("graph_expanded_rules", []),
            "conflicts": state.get("conflicts_detected", []),
        },
        "decision": {
            "verdict": state.get("verdict", ""),
            "cited_sections": state.get("cited_sections", []),
            "reasoning_summary": state.get("reasoning_summary", ""),
        },
        "tooling": {
            "proposed": state.get("allowed_tool_calls", []),
            "authorized": state.get("authorized_tool_calls", []),
            "blocked_by_guard": state.get("blocked_by_guard", []),
            "executed": list((state.get("raw_tool_outputs") or {}).keys()),
        },
        "filtering": {
            "redacted_fields": state.get("redacted_fields", []),
        },
        "response": state.get("response", ""),
        "metrics": {
            "llm_calls": 0,
            "latency_ms": 0,
        },
    }

    log_path = os.path.abspath(_LOG_PATH)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(log_entry) + "\n")

    state["decision_log"] = log_entry
    return state
