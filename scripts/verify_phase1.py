from gaggia_agent.state import default_state
from gaggia_agent.nodes.trust_tier_guard import trust_tier_guard
from gaggia_agent.nodes.tool_authorization_guard import tool_authorization_guard
from gaggia_agent.nodes.tool_executor import tool_executor
from gaggia_agent.nodes.output_filter import output_filter
from gaggia_agent.tools.mock_tools import reset_password, grant_file_access, lookup_employee

# 1. Red reset should be blocked
state = default_state(
    user_message="Reset my password",
    user_id="EMP-2011",
    trust_tier="red",
)
state["verdict"] = "allow"
state["risk_level"] = "low"
state["allowed_tool_calls"] = [
    {"tool": "reset_password", "args": {"employee_id": "EMP-2011"}}
]
state = trust_tier_guard(state)
state = tool_authorization_guard(state)
assert state["authorized_tool_calls"] == []
assert state["blocked_by_guard"]

# 2. Red escalation should be allowed
state = default_state(
    user_message="Get me a human",
    user_id="EMP-2011",
    trust_tier="red",
)
state["verdict"] = "escalate"
state["risk_level"] = "high"
state["allowed_tool_calls"] = [
    {
        "tool": "escalate_to_human",
        "args": {
            "reason": "User requested human help",
            "conversation_summary": "Test conversation",
        },
    }
]
state = trust_tier_guard(state)
state = tool_authorization_guard(state)
assert len(state["authorized_tool_calls"]) == 1

# 3. Service/admin/executive reset should not happen
assert reset_password("EMP-4010")["status"] == "not_reset"
assert reset_password("EMP-9000")["status"] == "not_reset"
assert reset_password("EMP-9001")["status"] == "not_reset"

# 4. Restricted/legal-hold/personal drives should not grant
assert grant_file_access("EMP-2200", "DRV-finance-restricted", "read", None)["status"] == "not_granted"
assert grant_file_access("EMP-2200", "DRV-legal-hold-2024", "read", None)["status"] == "not_granted"
assert grant_file_access("EMP-2200", "DRV-jessica-personal", "read", None)["status"] == "not_granted"

# 5. Output filter should block sensitive fields by default
state = default_state(
    user_message="Look up Sarah Chen",
    user_id="EMP-2200",
    trust_tier="blue",
)
state["raw_tool_outputs"] = {
    "lookup_employee_0": {
        "tool": "lookup_employee",
        "args": {"query": "Sarah Chen"},
        "output": lookup_employee("Sarah Chen"),
    }
}
state["output_constraints"] = {"allowed_fields": [], "blocked_fields": []}
state = output_filter(state)
out = state["filtered_tool_outputs"]["lookup_employee_0"]["output"]
assert "work_email" in out
assert "personal_email" not in out
assert "salary" not in out
assert "employment_status" not in out

# 6. Output filter should allow employment_status only when explicitly allowed
state = default_state(
    user_message="Is Jordan active?",
    user_id="EMP-1043",
    trust_tier="blue",
)
state["raw_tool_outputs"] = {
    "lookup_employee_0": {
        "tool": "lookup_employee",
        "args": {"query": "Jordan Rivera"},
        "output": lookup_employee("Jordan Rivera"),
    }
}
state["output_constraints"] = {
    "allowed_fields": ["employment_status"],
    "blocked_fields": [],
}
state = output_filter(state)
out = state["filtered_tool_outputs"]["lookup_employee_0"]["output"]
assert out["employment_status"] == "Active"

print("Phase 1 verification passed.")