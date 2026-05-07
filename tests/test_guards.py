"""
Pytest tests for GaggiaAgent Phase 1 deterministic guards and mock tools.
"""

from __future__ import annotations

import pytest

from gaggia_agent.nodes.output_filter import output_filter
from gaggia_agent.nodes.tool_authorization_guard import tool_authorization_guard
from gaggia_agent.nodes.trust_tier_guard import trust_tier_guard
from gaggia_agent.state import default_state
from gaggia_agent.tools.mock_tools import grant_file_access, reset_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides):
    state = default_state(
        user_message="test",
        user_id="USR-TEST-001",
        trust_tier=overrides.pop("trust_tier", "blue"),
    )
    for key, value in overrides.items():
        state[key] = value
    return state


# ---------------------------------------------------------------------------
# Guard tests
# ---------------------------------------------------------------------------

def test_red_user_reset_password_blocked():
    """Red user attempting reset_password must be blocked by tool_authorization_guard."""
    state = _make_state(
        trust_tier="red",
        verdict="allow",
        allowed_tool_calls=[
            {"tool": "reset_password", "args": {"employee_id": "EMP-2011"}}
        ],
    )
    state = trust_tier_guard(state)
    state = tool_authorization_guard(state)

    assert state["authorized_tool_calls"] == []
    blocked_tools = [b["tool"] for b in state["blocked_by_guard"]]
    assert "reset_password" in blocked_tools


def test_red_user_escalate_to_human_allowed():
    """Red user attempting escalate_to_human must be authorized."""
    state = _make_state(
        trust_tier="red",
        verdict="escalate",
        allowed_tool_calls=[
            {
                "tool": "escalate_to_human",
                "args": {
                    "reason": "User requested human help",
                    "conversation_summary": "Test",
                },
            }
        ],
    )
    state = trust_tier_guard(state)
    state = tool_authorization_guard(state)

    authorized_tools = [c["tool"] for c in state["authorized_tool_calls"]]
    assert "escalate_to_human" in authorized_tools


def test_blue_user_deny_verdict_blocks_all():
    """Blue user with deny verdict must have all tool calls blocked."""
    state = _make_state(
        trust_tier="blue",
        verdict="deny",
        allowed_tool_calls=[
            {"tool": "lookup_employee", "args": {"query": "Sarah Chen"}}
        ],
    )
    state = trust_tier_guard(state)
    state = tool_authorization_guard(state)

    assert state["authorized_tool_calls"] == []


def test_grey_high_risk_blocked_and_verdict_escalated():
    """Grey user with high-risk non-escalation tool must be blocked and verdict set to escalate."""
    state = _make_state(
        trust_tier="grey",
        risk_level="high",
        verdict="allow",
        allowed_tool_calls=[
            {"tool": "reset_password", "args": {"employee_id": "EMP-2011"}}
        ],
    )
    state = trust_tier_guard(state)
    state = tool_authorization_guard(state)

    assert state["authorized_tool_calls"] == []
    assert state["verdict"] == "escalate"


# ---------------------------------------------------------------------------
# Output filter tests
# ---------------------------------------------------------------------------

_SAMPLE_LOOKUP_OUTPUT = {
    "employee_id": "EMP-1042",
    "name": "Sarah Chen",
    "department": "Engineering",
    "title": "Senior Backend Engineer",
    "manager": "David Kim",
    "office": "Building 3, Floor 2",
    "work_email": "s.chen@gaggia.com",
    "work_phone": "x4521",
    "personal_email": "sarah.chen.personal@gmail.com",
    "personal_phone": "555-0147",
    "home_address": "742 Elm Street, Austin, TX",
    "salary": 158000,
    "performance_rating": "Exceeds Expectations",
    "employment_status": "Active",
}


def _state_with_lookup_output(output=None, output_constraints=None):
    state = _make_state(trust_tier="blue")
    state["raw_tool_outputs"] = {
        "lookup_employee_0": {
            "tool": "lookup_employee",
            "args": {"query": "Sarah Chen"},
            "output": output if output is not None else dict(_SAMPLE_LOOKUP_OUTPUT),
        }
    }
    state["output_constraints"] = output_constraints or {}
    return state


def test_output_filter_removes_personal_email_and_salary():
    """output_filter must remove personal_email and salary from lookup_employee output."""
    state = _state_with_lookup_output()
    state = output_filter(state)

    sanitized = state["filtered_tool_outputs"]["lookup_employee_0"]["output"]
    assert "personal_email" not in sanitized
    assert "salary" not in sanitized
    assert "personal_email" in state["redacted_fields"]
    assert "salary" in state["redacted_fields"]


def test_output_filter_keeps_work_email():
    """output_filter must preserve work_email in lookup_employee output."""
    state = _state_with_lookup_output()
    state = output_filter(state)

    sanitized = state["filtered_tool_outputs"]["lookup_employee_0"]["output"]
    assert "work_email" in sanitized
    assert sanitized["work_email"] == "s.chen@gaggia.com"


def test_output_filter_blocks_employment_status_by_default():
    """output_filter must block employment_status from lookup_employee by default."""
    state = _state_with_lookup_output()
    state = output_filter(state)

    sanitized = state["filtered_tool_outputs"]["lookup_employee_0"]["output"]
    assert "employment_status" not in sanitized


def test_output_filter_allows_employment_status_when_explicitly_permitted():
    """output_filter must keep employment_status when explicitly listed in allowed_fields."""
    state = _state_with_lookup_output(
        output_constraints={"allowed_fields": ["employment_status"], "blocked_fields": []}
    )
    state = output_filter(state)

    sanitized = state["filtered_tool_outputs"]["lookup_employee_0"]["output"]
    assert "employment_status" in sanitized
    assert sanitized["employment_status"] == "Active"


# ---------------------------------------------------------------------------
# Mock tool safety tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("employee_id", ["EMP-4010", "EMP-9000", "EMP-9001"])
def test_reset_password_refuses_privileged_accounts(employee_id: str):
    """reset_password must refuse service, admin, and executive accounts."""
    result = reset_password(employee_id)
    assert result["status"] == "not_reset"


@pytest.mark.parametrize(
    "drive_id",
    ["DRV-finance-restricted", "DRV-legal-hold-2024", "DRV-jessica-personal"],
)
def test_grant_file_access_refuses_prohibited_drives(drive_id: str):
    """grant_file_access must refuse restricted, legal-hold, and personal drives."""
    result = grant_file_access(
        employee_id="EMP-1042",
        drive_id=drive_id,
        access_level="read",
        duration_days=7,
    )
    assert result["status"] == "not_granted"
