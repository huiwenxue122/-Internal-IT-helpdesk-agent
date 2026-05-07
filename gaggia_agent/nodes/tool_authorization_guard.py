from gaggia_agent.state import AgentState
from gaggia_agent.tools.registry import TOOL_REGISTRY


def tool_authorization_guard(state: AgentState) -> AgentState:
    state["authorized_tool_calls"] = []
    state["blocked_by_guard"] = []

    verdict = state.get("verdict", "")
    trust_tier = state.get("trust_tier", "")
    risk_level = state.get("risk_level", "")
    allowed_tools_by_trust = state.get("allowed_tools_by_trust", [])

    for call in state.get("allowed_tool_calls", []):
        tool = call.get("tool", "")
        args = call.get("args", {})

        blocked_reason = _check(
            tool=tool,
            verdict=verdict,
            trust_tier=trust_tier,
            risk_level=risk_level,
            allowed_tools_by_trust=allowed_tools_by_trust,
            state=state,
        )

        if blocked_reason:
            state["blocked_by_guard"].append(
                {"tool": tool, "args": args, "blocked_reason": blocked_reason}
            )
            # Escalate verdict when grey+high-risk forces a block, or when an
            # unverified Grey requester is blocked from grant_file_access.
            if trust_tier == "grey" and tool == "grant_file_access":
                state["verdict"] = "clarify"
            elif (
                trust_tier == "grey"
                and risk_level == "high"
                and tool != "escalate_to_human"
                and blocked_reason.startswith("Team Grey high-risk")
            ):
                state["verdict"] = "escalate"
        else:
            state["authorized_tool_calls"].append(call)

    return state


def _check(
    tool: str,
    verdict: str,
    trust_tier: str,
    risk_level: str,
    allowed_tools_by_trust: list[str],
    state: AgentState | None = None,
) -> str | None:
    if verdict not in ("allow", "escalate"):
        return "Policy verdict is not allow or escalate."

    if tool not in TOOL_REGISTRY:
        return "Unknown tool."

    if tool not in allowed_tools_by_trust:
        return "Tool is not allowed for this trust tier."

    if trust_tier == "red" and tool != "escalate_to_human":
        return "Team Red users cannot execute non-escalation tools."

    if trust_tier == "grey" and risk_level == "high" and tool != "escalate_to_human":
        return "Team Grey high-risk actions require clarification or escalation."

    # Grey users may not execute grant_file_access unless explicitly verified.
    # Unverified / partially-verified Grey requesters cannot self-approve drive access.
    if trust_tier == "grey" and tool == "grant_file_access":
        requester_profile = (state or {}).get("requester_profile") or {}
        # verified=True must be explicitly set; absence or False blocks the grant.
        if not requester_profile.get("verified", False):
            return (
                "Grey-tier unverified requester cannot execute grant_file_access. "
                "Manager or drive-owner approval required (§4.2)."
            )

    return None
