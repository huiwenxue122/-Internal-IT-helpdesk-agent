from __future__ import annotations

import re
from typing import List, Optional

from gaggia_agent.policy.models import PolicyRule

_SCORE_THRESHOLD = 6
_MAX_RESULTS = 8

# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    """Return lowercase word tokens of 4+ characters, splitting on _ and spaces."""
    tokens: set[str] = set()
    for word in re.findall(r"\w+", text.lower()):
        for part in word.split("_"):
            if len(part) >= 4:
                tokens.add(part)
    return tokens


# ---------------------------------------------------------------------------
# Query hint extraction
# ---------------------------------------------------------------------------

def _extract_query_hints(
    user_message: str,
    intent: str,
    requested_fields: list[str],
) -> dict[str, set[str]]:
    """
    Extract data_type and resource_type hints from free-text context.
    Returns {"data_hints": set, "resource_hints": set}.
    """
    combined = " ".join([user_message, intent] + requested_fields).lower()

    resource_hints: set[str] = set()
    data_hints: set[str] = set()

    # Resource type hints
    if "legal-hold" in combined or "legal hold" in combined or "legalhold" in combined:
        resource_hints.add("legal_hold_drive")
    if "restricted" in combined:
        resource_hints.add("restricted_drive")
    if "personal drive" in combined:
        resource_hints.add("personal_drive")
    if "service account" in combined or "svc-" in combined:
        resource_hints.add("service_account")
    if "admin account" in combined or "sysadmin" in combined:
        resource_hints.add("admin_account")
    if "executive" in combined:
        resource_hints.add("executive_account")
    if "standard account" in combined or "standard employee" in combined:
        resource_hints.add("standard_account")

    # Data type hints (only contribute when not already in requested_fields)
    if "salary" in combined or "compensation" in combined or "bonus" in combined:
        data_hints.update({"salary", "compensation", "bonus_target"})
    if "performance review" in combined or "performance rating" in combined:
        data_hints.update({"performance_review", "performance_rating"})
    if "personal email" in combined or "home address" in combined or "personal phone" in combined:
        data_hints.update({"personal_email", "personal_phone", "home_address"})
    # Only infer employment_status from phrases that unambiguously refer to an
    # employee's active-employment state.  "active" alone is too broad — it appears
    # in "active investigation", "active incident", "active directory", etc.
    _EMPLOYMENT_ACTIVE_PHRASES = (
        "currently active",
        "active status",
        "still works here",
        "still employed",
        "still with the company",
        "works here",
        "employee active",
        "account active",
        "still active",
        "currently employed",
    )
    if any(phrase in combined for phrase in _EMPLOYMENT_ACTIVE_PHRASES):
        data_hints.add("employment_status")
    if "termination" in combined or " fired" in combined or "resignation" in combined:
        data_hints.update({"termination_details", "resignation_details", "employment_status_change"})

    return {"data_hints": data_hints, "resource_hints": resource_hints}


# ---------------------------------------------------------------------------
# Rule scorer
# ---------------------------------------------------------------------------

def _score_rule(
    rule: PolicyRule,
    intent: str,
    requested_fields: list[str],
    candidate_tools: list[str],
    risk_level: str,
    trust_tier: str,
    resource_hints: set[str],
    extra_data_hints: set[str],
    query_tokens: set[str],
    adversarial_signals: list[str],
) -> int:
    score = 0

    # Pre-compute scope booleans used for tool match gating.
    rule_tokens = _tokenize(rule.text)

    data_scope_matched = bool(
        requested_fields and any(f in rule.data_types for f in requested_fields)
    )
    resource_scope_matched = bool(
        resource_hints and rule.resource_types
        and any(rh in rule.resource_types for rh in resource_hints)
    )
    action_matched = bool(
        intent and rule.action
        and (intent == rule.action or rule.action in intent or intent in rule.action)
    )
    keyword_scope_matched = bool(query_tokens and (query_tokens & rule_tokens))

    # +6: exact match between requested_fields and rule.data_types
    if data_scope_matched:
        score += 6

    # Tool match — trust-tier gated, PLUS data/resource scope gating for
    # rules that declare specific data_types or resource_types.
    #
    # Rationale: lookup_employee is a broad tool.  A rule like
    # rule_active_status_manager_exception that governs only employment_status
    # should not score 5 just because lookup_employee was requested for a
    # salary query.  Full credit (+5) requires the query to also match the
    # rule's domain through data, resource, action, or keyword signals.
    # Without that corroboration the tool match contributes only +1
    # (a weak boost that cannot reach threshold on its own).
    if candidate_tools and rule.tools:
        trust_ok = (not rule.trust_tiers) or (trust_tier in rule.trust_tiers)
        if trust_ok and any(t in rule.tools for t in candidate_tools):
            if rule.data_types or rule.resource_types:
                # Scoped rule: full credit only when query scope also matches
                if data_scope_matched or resource_scope_matched or action_matched or keyword_scope_matched:
                    score += 5
                else:
                    score += 1  # weak boost — below threshold by itself
            else:
                # No scope restriction declared: always give full tool match credit
                score += 5

    # +5: trust tier explicitly named in the rule
    if trust_tier and rule.trust_tiers and trust_tier in rule.trust_tiers:
        score += 5

    # +5: intent / action match
    if action_matched:
        score += 5

    # +4: resource hint matches rule.resource_types
    if resource_scope_matched:
        score += 4

    # +3: extra data hints match rule.data_types (beyond what's in requested_fields)
    if extra_data_hints and rule.data_types:
        if any(dh in rule.data_types for dh in extra_data_hints):
            score += 3

    # +3: keyword match between query tokens and rule text
    if keyword_scope_matched:
        score += 3

    # +1: risk boost — high risk query + high risk rule, boost only, not a trigger
    if risk_level == "high" and rule.risk_level == "high":
        score += 1

    # +6: adversarial signal present and this is the prompt injection rule
    if adversarial_signals and rule.rule_id == "rule_prompt_injection_denied":
        if any(
            sig_word in sig
            for sig in adversarial_signals
            for sig_word in ("inject", "ignore", "override", "prompt")
        ):
            score += 6

    # +6: claimed-authority signal and this is the claimed authority rule
    if adversarial_signals and rule.rule_id == "rule_claimed_authority_insufficient":
        if any(
            sig_word in sig
            for sig in adversarial_signals
            for sig_word in ("claim", "authority", "approved", "ciso")
        ):
            score += 6

    return score


# ---------------------------------------------------------------------------
# Graph class
# ---------------------------------------------------------------------------

class InMemoryPolicyGraph:
    def __init__(self, rules: Optional[List[PolicyRule]] = None) -> None:
        self._rules: dict[str, PolicyRule] = {}
        if rules:
            self.load_rules(rules)

    def available(self) -> bool:
        return True

    def load_rules(self, rules: List[PolicyRule]) -> None:
        for rule in rules:
            self._rules[rule.rule_id] = rule

    def get_rules_by_ids(self, rule_ids: List[str]) -> List[PolicyRule]:
        return [self._rules[rid] for rid in rule_ids if rid in self._rules]

    def find_rules_for_query_context(
        self,
        intent: str,
        requested_fields: List[str],
        candidate_tools: List[str],
        risk_level: str,
        trust_tier: str,
        user_message: str = "",
        adversarial_signals: Optional[List[str]] = None,
    ) -> List[PolicyRule]:
        if adversarial_signals is None:
            adversarial_signals = []

        hints = _extract_query_hints(user_message, intent, requested_fields)
        resource_hints = hints["resource_hints"]
        # Extra data hints: hints beyond what the caller already declared in requested_fields
        extra_data_hints = hints["data_hints"] - set(requested_fields)

        # Build query token set from user_message + requested_fields only.
        # Intent is already handled by the dedicated action_matched (+5) signal;
        # including it here causes tokens like "employee" (from
        # "employee_hr_data_lookup") to match virtually every HR rule text,
        # producing false keyword_scope_matched hits.
        query_tokens: set[str] = set()
        for field in requested_fields:
            query_tokens |= _tokenize(field)
        if user_message:
            query_tokens |= _tokenize(user_message)

        scored: list[tuple[int, PolicyRule]] = []
        for rule in self._rules.values():
            s = _score_rule(
                rule=rule,
                intent=intent,
                requested_fields=requested_fields,
                candidate_tools=candidate_tools,
                risk_level=risk_level,
                trust_tier=trust_tier,
                resource_hints=resource_hints,
                extra_data_hints=extra_data_hints,
                query_tokens=query_tokens,
                adversarial_signals=adversarial_signals,
            )
            if s >= _SCORE_THRESHOLD:
                scored.append((s, rule))

        # Sort: score desc → precedence desc → rule_id asc
        scored.sort(key=lambda x: (-x[0], -x[1].precedence, x[1].rule_id))
        return [rule for _, rule in scored[:_MAX_RESULTS]]

    def expand_related_rules(
        self,
        rule_ids: List[str],
        depth: int = 1,
    ) -> List[PolicyRule]:
        """
        Follow only forward links (exception_to, overrides, references) from
        each seed rule.  Reverse links are intentionally excluded: a rule that
        declares an exception-to relationship should be discovered by the scorer
        when the query actually asks about its domain, not by backwards traversal
        from an unrelated seed.  This prevents, for example, rule_active_status_
        manager_exception from appearing in a salary query just because
        rule_individual_hr_records_denied was retrieved.
        """
        if not rule_ids:
            return []

        visited: set[str] = set(rule_ids)
        frontier: set[str] = set(rule_ids)

        for _ in range(depth):
            next_frontier: set[str] = set()
            for rid in frontier:
                rule = self._rules.get(rid)
                if rule is None:
                    continue
                for linked_id in rule.exception_to + rule.overrides + rule.references:
                    if linked_id not in visited:
                        next_frontier.add(linked_id)
            visited.update(next_frontier)
            frontier = next_frontier
            if not frontier:
                break

        return [
            self._rules[rid]
            for rid in visited - set(rule_ids)
            if rid in self._rules
        ]
