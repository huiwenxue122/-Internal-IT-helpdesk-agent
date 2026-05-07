from __future__ import annotations

import hashlib
from gaggia_agent.policy.models import PolicyConflict, PolicyRule
from gaggia_agent.state import AgentState

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _max_risk(a: str, b: str) -> str:
    return a if _RISK_ORDER.get(a, 0) >= _RISK_ORDER.get(b, 0) else b


def _conflict_id(rule_ids: list[str], conflict_type: str) -> str:
    key = conflict_type + ":" + ":".join(sorted(rule_ids))
    return "CONFLICT-" + hashlib.md5(key.encode()).hexdigest()[:8].upper()


def has_scope_overlap(rule_a: PolicyRule, rule_b: PolicyRule) -> bool:
    """
    Return True if two rules share enough scope to constitute a real conflict.

    Scope overlap means at least one of:
    - same non-empty action
    - overlapping tools
    - overlapping data_types
    - overlapping resource_types
    - overlapping trust_tiers
    """
    if rule_a.action and rule_b.action and rule_a.action == rule_b.action:
        return True
    if set(rule_a.tools) & set(rule_b.tools):
        return True
    if set(rule_a.data_types) & set(rule_b.data_types):
        return True
    if set(rule_a.resource_types) & set(rule_b.resource_types):
        return True
    if set(rule_a.trust_tiers) & set(rule_b.trust_tiers):
        return True
    return False


def _rules_from_state(state: AgentState) -> list[PolicyRule]:
    combined: list[PolicyRule] = []
    seen: set[str] = set()
    for raw in list(state.get("retrieved_rules", [])) + list(state.get("graph_expanded_rules", [])):
        rule = PolicyRule.from_dict(raw)
        if rule.rule_id not in seen:
            combined.append(rule)
            seen.add(rule.rule_id)
    return combined


def conflict_detector(state: AgentState) -> AgentState:
    """
    Detect policy conflicts in the evidence bundle already in state.

    Produces three kinds of conflicts:
    - explicit_exception  — a rule has exception_to links whose base is in scope
    - explicit_override   — a rule has overrides links whose target is in scope
    - implicit_modality_conflict — a may/must_not pair that shares action/tool/data scope

    Conflicts are only reported when both rules are present in the combined
    retrieved evidence AND their scopes overlap.  This prevents irrelevant
    cross-domain conflicts from polluting the evidence bundle.

    This node never resolves conflicts; it surfaces them as risk signals
    for the later Policy Reasoning Agent.
    """
    rules = _rules_from_state(state)
    rule_index: dict[str, PolicyRule] = {r.rule_id: r for r in rules}

    conflicts: list[PolicyConflict] = []
    seen_keys: set[str] = set()

    # ------------------------------------------------------------------
    # Explicit exception conflicts
    # ------------------------------------------------------------------
    for rule in rules:
        for exc_id in rule.exception_to:
            # Both rules must be present in the evidence bundle
            if exc_id not in rule_index:
                continue

            base_rule = rule_index[exc_id]

            # Require scope overlap — prevents cross-domain false positives
            if not has_scope_overlap(rule, base_rule):
                continue

            ids = sorted([rule.rule_id, exc_id])
            key = "explicit_exception:" + ":".join(ids)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            conflicts.append(
                PolicyConflict(
                    conflict_id=_conflict_id(ids, "explicit_exception"),
                    conflict_type="explicit_exception",
                    rule_ids=[rule.rule_id, exc_id],
                    section_ids=list({rule.section_id, base_rule.section_id}),
                    risk_level=_max_risk(rule.risk_level, base_rule.risk_level),
                    resolution_hint=(
                        "Specific exception applies only when all required conditions "
                        "are satisfied; otherwise the broader prohibition remains in force."
                    ),
                )
            )

    # ------------------------------------------------------------------
    # Explicit override conflicts
    # ------------------------------------------------------------------
    for rule in rules:
        for ov_id in rule.overrides:
            if ov_id not in rule_index:
                continue

            target_rule = rule_index[ov_id]
            if not has_scope_overlap(rule, target_rule):
                continue

            ids = sorted([rule.rule_id, ov_id])
            key = "explicit_override:" + ":".join(ids)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            conflicts.append(
                PolicyConflict(
                    conflict_id=_conflict_id(ids, "explicit_override"),
                    conflict_type="explicit_override",
                    rule_ids=[rule.rule_id, ov_id],
                    section_ids=list({rule.section_id, target_rule.section_id}),
                    risk_level=_max_risk(rule.risk_level, target_rule.risk_level),
                    resolution_hint=(
                        "Higher-precedence rule overrides lower-precedence rule only "
                        "within its stated scope."
                    ),
                )
            )

    # ------------------------------------------------------------------
    # Implicit modality conflicts (may vs. must_not)
    # ------------------------------------------------------------------
    for i, rule_a in enumerate(rules):
        for rule_b in rules[i + 1:]:
            if not _is_implicit_conflict(rule_a, rule_b):
                continue

            ids = sorted([rule_a.rule_id, rule_b.rule_id])
            key = "implicit_modality_conflict:" + ":".join(ids)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            conflicts.append(
                PolicyConflict(
                    conflict_id=_conflict_id(ids, "implicit_modality_conflict"),
                    conflict_type="implicit_modality_conflict",
                    rule_ids=ids,
                    section_ids=list({rule_a.section_id, rule_b.section_id}),
                    risk_level=_max_risk(rule_a.risk_level, rule_b.risk_level),
                    resolution_hint=(
                        "Implicit may-vs-must-not conflict. If no explicit exception or "
                        "override applies, prefer denial, clarification, or escalation."
                    ),
                )
            )

    state["conflicts_detected"] = [c.to_dict() for c in conflicts]
    return state


def _is_implicit_conflict(rule_a: PolicyRule, rule_b: PolicyRule) -> bool:
    modalities = {rule_a.modality, rule_b.modality}
    if modalities != {"may", "must_not"}:
        return False

    # Must share action OR tool
    action_overlap = bool(
        rule_a.action and rule_b.action and rule_a.action == rule_b.action
    ) or bool(set(rule_a.tools) & set(rule_b.tools))

    if not action_overlap:
        return False

    # Must share data_type, resource_type, OR trust_tier
    return (
        bool(set(rule_a.data_types) & set(rule_b.data_types))
        or bool(set(rule_a.resource_types) & set(rule_b.resource_types))
        or bool(set(rule_a.trust_tiers) & set(rule_b.trust_tiers))
    )
