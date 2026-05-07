from __future__ import annotations

from gaggia_agent.state import AgentState

DEFAULT_FORBIDDEN: frozenset[str] = frozenset(
    {
        "personal_email",
        "personal_phone",
        "home_address",
        "salary",
        "bonus_target",
        "last_review",
        "performance_rating",
        "disciplinary_actions",
        "employment_status",
    }
)

DIRECTORY_ALLOWED: frozenset[str] = frozenset(
    {
        "employee_id",
        "name",
        "department",
        "title",
        "manager",
        "office",
        "work_email",
        "work_phone",
    }
)


def output_filter(state: AgentState) -> AgentState:
    output_constraints = state.get("output_constraints") or {}
    explicitly_allowed: set[str] = set(output_constraints.get("allowed_fields", []))
    explicitly_blocked: set[str] = set(output_constraints.get("blocked_fields", []))

    redacted: list[str] = list(state.get("redacted_fields") or [])
    filtered: dict = {}

    for key, entry in (state.get("raw_tool_outputs") or {}).items():
        tool_name = entry.get("tool", "")
        raw_output = entry.get("output")

        if raw_output is None:
            filtered[key] = dict(entry)
            continue

        sanitized, newly_redacted = _filter_value(
            value=raw_output,
            tool_name=tool_name,
            explicitly_allowed=explicitly_allowed,
            explicitly_blocked=explicitly_blocked,
        )
        redacted.extend(newly_redacted)

        filtered_entry = dict(entry)
        filtered_entry["output"] = sanitized
        filtered[key] = filtered_entry

    state["filtered_tool_outputs"] = filtered
    state["redacted_fields"] = redacted
    return state


def _filter_value(
    value: object,
    tool_name: str,
    explicitly_allowed: set[str],
    explicitly_blocked: set[str],
) -> tuple[object, list[str]]:
    if not isinstance(value, dict):
        return value, []

    sanitized: dict = {}
    redacted: list[str] = []

    for field, field_value in value.items():
        if field in explicitly_blocked:
            redacted.append(field)
            continue

        if tool_name == "lookup_employee":
            permitted = DIRECTORY_ALLOWED | explicitly_allowed
            if field not in permitted:
                redacted.append(field)
                continue
        else:
            if field in DEFAULT_FORBIDDEN and field not in explicitly_allowed:
                redacted.append(field)
                continue

        if isinstance(field_value, dict):
            nested, nested_redacted = _filter_value(
                field_value, tool_name, explicitly_allowed, explicitly_blocked
            )
            sanitized[field] = nested
            redacted.extend(nested_redacted)
        else:
            sanitized[field] = field_value

    return sanitized, redacted
