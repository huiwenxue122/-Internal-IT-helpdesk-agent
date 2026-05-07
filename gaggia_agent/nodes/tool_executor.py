import inspect

from gaggia_agent.state import AgentState
from gaggia_agent.tools.registry import TOOL_REGISTRY


def _filter_args(fn: object, args: dict) -> dict:
    """Return only the kwargs that the function actually accepts.

    LLMs sometimes emit extra fields (e.g. ``name`` alongside ``query``)
    that the mock tool functions don't declare.  Filtering them here
    prevents TypeError while preserving all valid arguments.
    """
    try:
        sig = inspect.signature(fn)  # type: ignore[arg-type]
        params = sig.parameters
        # If the function accepts **kwargs, pass everything through.
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        if has_var_keyword:
            return args
        return {k: v for k, v in args.items() if k in params}
    except (TypeError, ValueError):
        return args


def tool_executor(state: AgentState) -> AgentState:
    if not state.get("raw_tool_outputs"):
        state["raw_tool_outputs"] = {}

    for index, call in enumerate(state.get("authorized_tool_calls", [])):
        tool_name = call.get("tool", "")
        args = call.get("args", {})
        key = f"{tool_name}_{index}"

        try:
            tool_fn = TOOL_REGISTRY[tool_name]["function"]
            filtered_args = _filter_args(tool_fn, args)
            output = tool_fn(**filtered_args)
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
