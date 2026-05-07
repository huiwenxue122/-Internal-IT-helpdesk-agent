from gaggia_agent.state import AgentState
from gaggia_agent.tools.registry import ALL_TOOL_NAMES


def trust_tier_guard(state: AgentState) -> AgentState:
    tier = state["trust_tier"]

    if tier == "red":
        state["allowed_tools_by_trust"] = ["escalate_to_human"]
        state["trust_constraints"].append(
            "User Trust Tiers: Team Red users cannot execute tool calls except escalate_to_human."
        )
    elif tier == "grey":
        state["allowed_tools_by_trust"] = list(ALL_TOOL_NAMES)
        state["trust_constraints"].append(
            "User Trust Tiers: Team Grey users require additional caution; "
            "high-risk actions should clarify or escalate."
        )
    elif tier == "blue":
        state["allowed_tools_by_trust"] = list(ALL_TOOL_NAMES)
        state["trust_constraints"].append(
            "User Trust Tiers: Team Blue users are verified employees, "
            "but policy restrictions still apply."
        )
    else:
        state["trust_tier"] = "grey"
        state["allowed_tools_by_trust"] = list(ALL_TOOL_NAMES)
        state["trust_constraints"].append(
            "Unknown trust tier treated as Team Grey; additional caution required."
        )

    return state
