from gaggia_agent.state import AgentState
from gaggia_agent.tools.registry import TOOL_REGISTRY


def tool_executor(state: AgentState) -> AgentState:
    if not state.get("raw_tool_outputs"):
        state["raw_tool_outputs"] = {}

    for index, call in enumerate(state.get("authorized_tool_calls", [])):
        tool_name = call.get("tool", "")
        args = call.get("args", {})
        key = f"{tool_name}_{index}"

        try:
            tool_fn = TOOL_REGISTRY[tool_name]["function"]
            output = tool_fn(**args)
            state["raw_tool_outputs"][key] = {
                "tool": tool_name,
                "args": args,
                "output": output,
            }
        except Exception as exc:
            state["raw_tool_outputs"][key] = {
                "tool": tool_name,
                "args": args,
                "error": str(exc),
            }

    return state
