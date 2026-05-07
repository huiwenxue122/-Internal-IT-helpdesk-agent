"""
Schema shapes for LLM agent I/O.

Used for prompt construction and output validation.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Router Agent output schema
# ---------------------------------------------------------------------------

ROUTER_OUTPUT_SCHEMA: dict = {
    "intent": "str  # account_password_reset | employee_directory_lookup | employee_hr_data_lookup | file_access_request | general_hr_policy_question | human_escalation_request | general_helpdesk_request",
    "target_entities": "list[{type: employee|employee_id|drive_id|unknown, value: str}]",
    "requested_fields": "list[str]  # e.g. salary, work_email, employment_status, ...",
    "candidate_tools": "list[str]  # subset of: reset_password, lookup_employee, grant_file_access, query_hr_database, escalate_to_human",
    "risk_level": "low | medium | high",
    "adversarial_signals": "list[str]  # prompt_injection | claimed_authority | urgency",
    "notes": "str",
}

ROUTER_OUTPUT_EXAMPLE: dict = {
    "intent": "employee_directory_lookup",
    "target_entities": [{"type": "employee", "value": "Sarah Chen"}],
    "requested_fields": ["work_email"],
    "candidate_tools": ["lookup_employee"],
    "risk_level": "low",
    "adversarial_signals": [],
    "notes": "User requests a work email for a named employee.",
}

VALID_INTENTS = {
    "account_password_reset",
    "employee_directory_lookup",
    "employee_hr_data_lookup",
    "file_access_request",
    "general_hr_policy_question",
    "human_escalation_request",
    "general_helpdesk_request",
}

VALID_RISK_LEVELS = {"low", "medium", "high"}

# ---------------------------------------------------------------------------
# Policy Reasoning Agent output schema
# ---------------------------------------------------------------------------

POLICY_DECISION_SCHEMA: dict = {
    "verdict": "allow | deny | clarify | escalate",
    "cited_sections": "list[str]  # e.g. ['5.2', '7.3']",
    "reasoning_summary": "str  # concise explanation, no user-facing prose",
    "allowed_tool_calls": "list[{tool: str, args: dict, reason: str}]",
    "blocked_tool_calls": "list[{tool: str, blocked_reason: str}]",
    "output_constraints": {
        "allowed_fields": "list[str]",
        "blocked_fields": "list[str]",
        "minimal_response_fields": "list[str]",
    },
    "confidence": "low | medium | high",
}

POLICY_DECISION_EXAMPLE: dict = {
    "verdict": "allow",
    "cited_sections": ["3.1", "3.3"],
    "reasoning_summary": "Verified employee requested work email. Directory field allowed per §3.1.",
    "allowed_tool_calls": [
        {"tool": "lookup_employee", "args": {"query": "Sarah Chen"}, "reason": "Directory lookup"}
    ],
    "blocked_tool_calls": [],
    "output_constraints": {
        "allowed_fields": ["employee_id", "name", "department", "title", "manager", "office", "work_email", "work_phone"],
        "blocked_fields": ["personal_email", "personal_phone", "home_address", "salary"],
        "minimal_response_fields": ["work_email"],
    },
    "confidence": "high",
}

VALID_VERDICTS = {"allow", "deny", "clarify", "escalate"}
VALID_CONFIDENCE = {"low", "medium", "high"}

# ---------------------------------------------------------------------------
# Response Agent output schema
# ---------------------------------------------------------------------------

RESPONSE_OUTPUT_SCHEMA: dict = {
    "response": "str  # user-facing text only; no internal reasoning or raw data",
}
