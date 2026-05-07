from gaggia_agent.tools.mock_tools import (
    escalate_to_human,
    grant_file_access,
    lookup_employee,
    query_hr_database,
    reset_password,
)

TOOL_REGISTRY: dict = {
    "reset_password": {
        "function": reset_password,
        "side_effecting": True,
        "sensitive_outputs": ["temp_password"],
    },
    "lookup_employee": {
        "function": lookup_employee,
        "side_effecting": False,
        "sensitive_outputs": [
            "personal_email",
            "personal_phone",
            "home_address",
            "salary",
            "performance_rating",
            "employment_status",
        ],
    },
    "grant_file_access": {
        "function": grant_file_access,
        "side_effecting": True,
        "sensitive_outputs": [],
    },
    "query_hr_database": {
        "function": query_hr_database,
        "side_effecting": False,
        "sensitive_outputs": [
            "salary",
            "bonus_target",
            "last_review",
            "performance_rating",
            "disciplinary_actions",
        ],
    },
    "escalate_to_human": {
        "function": escalate_to_human,
        "side_effecting": True,
        "sensitive_outputs": [],
    },
}

ALL_TOOL_NAMES: list[str] = list(TOOL_REGISTRY.keys())
