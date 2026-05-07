"""
Neo4j-backed policy graph.

Uses environment variables NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD.
If credentials are absent or the connection fails, available() returns False
and callers should fall back to InMemoryPolicyGraph.
"""

from __future__ import annotations

import json
import os
from typing import List

from gaggia_agent.policy.models import PolicyRule


class Neo4jPolicyGraph:
    def __init__(self) -> None:
        self._driver = None
        self._connected = False
        self._try_connect()

    def _try_connect(self) -> None:
        uri = os.environ.get("NEO4J_URI", "")
        username = os.environ.get("NEO4J_USERNAME", "")
        password = os.environ.get("NEO4J_PASSWORD", "")

        if not (uri and username and password):
            return

        try:
            from neo4j import GraphDatabase  # type: ignore

            driver = GraphDatabase.driver(uri, auth=(username, password))
            driver.verify_connectivity()
            self._driver = driver
            self._connected = True
        except Exception:
            self._driver = None
            self._connected = False

    def available(self) -> bool:
        return self._connected and self._driver is not None

    def close(self) -> None:
        if self._driver:
            try:
                self._driver.close()
            except Exception:
                pass
        self._driver = None
        self._connected = False

    def clear_graph(self) -> None:
        if not self.available():
            return
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def load_rules(self, rules: List[PolicyRule]) -> None:
        if not self.available():
            return

        with self._driver.session() as session:
            for rule in rules:
                session.run(
                    """
                    MERGE (r:Rule {rule_id: $rule_id})
                    SET r.section_id = $section_id,
                        r.text = $text,
                        r.modality = $modality,
                        r.domain = $domain,
                        r.action = $action,
                        r.precedence = $precedence,
                        r.risk_level = $risk_level,
                        r.data_types = $data_types,
                        r.resource_types = $resource_types,
                        r.tools = $tools,
                        r.trust_tiers = $trust_tiers,
                        r.conditions = $conditions,
                        r.references = $references,
                        r.exception_to = $exception_to,
                        r.overrides = $overrides
                    """,
                    rule_id=rule.rule_id,
                    section_id=rule.section_id,
                    text=rule.text,
                    modality=rule.modality,
                    domain=rule.domain,
                    action=rule.action or "",
                    precedence=rule.precedence,
                    risk_level=rule.risk_level,
                    data_types=rule.data_types,
                    resource_types=rule.resource_types,
                    tools=rule.tools,
                    trust_tiers=rule.trust_tiers,
                    conditions=rule.conditions,
                    references=rule.references,
                    exception_to=rule.exception_to,
                    overrides=rule.overrides,
                )

                # Section node
                session.run(
                    """
                    MERGE (s:Section {section_id: $section_id})
                    WITH s
                    MATCH (r:Rule {rule_id: $rule_id})
                    MERGE (s)-[:CONTAINS]->(r)
                    """,
                    section_id=rule.section_id,
                    rule_id=rule.rule_id,
                )

                for dt in rule.data_types:
                    session.run(
                        """
                        MERGE (d:DataType {name: $name})
                        WITH d
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (r)-[:GOVERNS_DATA]->(d)
                        """,
                        name=dt,
                        rule_id=rule.rule_id,
                    )

                for tool in rule.tools:
                    session.run(
                        """
                        MERGE (t:Tool {name: $name})
                        WITH t
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (r)-[:GOVERNS_TOOL]->(t)
                        """,
                        name=tool,
                        rule_id=rule.rule_id,
                    )

                for rt in rule.resource_types:
                    session.run(
                        """
                        MERGE (res:ResourceType {name: $name})
                        WITH res
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (r)-[:GOVERNS_RESOURCE]->(res)
                        """,
                        name=rt,
                        rule_id=rule.rule_id,
                    )

                for tier in rule.trust_tiers:
                    session.run(
                        """
                        MERGE (tt:TrustTier {name: $name})
                        WITH tt
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (r)-[:APPLIES_TO_TRUST_TIER]->(tt)
                        """,
                        name=tier,
                        rule_id=rule.rule_id,
                    )

                for cond in rule.conditions:
                    session.run(
                        """
                        MERGE (c:Condition {name: $name})
                        WITH c
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (r)-[:REQUIRES]->(c)
                        """,
                        name=cond,
                        rule_id=rule.rule_id,
                    )

                for ref in rule.references:
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (target:Rule {rule_id: $target_id})
                        MERGE (r)-[:REFERENCES]->(target)
                        """,
                        rule_id=rule.rule_id,
                        target_id=ref,
                    )

                for exc in rule.exception_to:
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (target:Rule {rule_id: $target_id})
                        MERGE (r)-[:EXCEPTION_TO]->(target)
                        """,
                        rule_id=rule.rule_id,
                        target_id=exc,
                    )

                for ov in rule.overrides:
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        MERGE (target:Rule {rule_id: $target_id})
                        MERGE (r)-[:OVERRIDES]->(target)
                        """,
                        rule_id=rule.rule_id,
                        target_id=ov,
                    )

    def _row_to_rule(self, row: dict) -> PolicyRule:
        def _list(val) -> list:
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return [val] if val else []
            return []

        return PolicyRule(
            rule_id=row.get("rule_id", ""),
            section_id=row.get("section_id", ""),
            text=row.get("text", ""),
            modality=row.get("modality", "may"),
            domain=row.get("domain", "general"),
            action=row.get("action") or None,
            data_types=_list(row.get("data_types", [])),
            resource_types=_list(row.get("resource_types", [])),
            tools=_list(row.get("tools", [])),
            trust_tiers=_list(row.get("trust_tiers", [])),
            conditions=_list(row.get("conditions", [])),
            precedence=int(row.get("precedence", 50)),
            risk_level=row.get("risk_level", "low"),
            references=_list(row.get("references", [])),
            exception_to=_list(row.get("exception_to", [])),
            overrides=_list(row.get("overrides", [])),
        )

    def get_rules_by_ids(self, rule_ids: List[str]) -> List[PolicyRule]:
        if not self.available() or not rule_ids:
            return []

        with self._driver.session() as session:
            result = session.run(
                "MATCH (r:Rule) WHERE r.rule_id IN $ids RETURN r",
                ids=rule_ids,
            )
            return [self._row_to_rule(dict(record["r"])) for record in result]

    def find_rules_for_query_context(
        self,
        intent: str,
        requested_fields: List[str],
        candidate_tools: List[str],
        risk_level: str,
        trust_tier: str,
        user_message: str = "",
        adversarial_signals: List[str] | None = None,
    ) -> List[PolicyRule]:
        if not self.available():
            return []

        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (r:Rule)
                WHERE
                    any(t IN r.trust_tiers WHERE t = $trust_tier)
                    OR any(tool IN r.tools WHERE tool IN $candidate_tools)
                    OR any(dt IN r.data_types WHERE dt IN $requested_fields)
                    OR r.action = $intent
                    OR ($risk_level = 'high' AND r.risk_level = 'high')
                RETURN r
                """,
                trust_tier=trust_tier,
                candidate_tools=candidate_tools,
                requested_fields=requested_fields,
                intent=intent,
                risk_level=risk_level,
            )
            return [self._row_to_rule(dict(record["r"])) for record in result]

    def expand_related_rules(
        self,
        rule_ids: List[str],
        depth: int = 2,
    ) -> List[PolicyRule]:
        if not self.available() or not rule_ids:
            return []

        with self._driver.session() as session:
            result = session.run(
                f"""
                MATCH (r:Rule) WHERE r.rule_id IN $ids
                CALL {{
                    WITH r
                    MATCH (r)-[:REFERENCES|EXCEPTION_TO|OVERRIDES*1..{depth}]->(related:Rule)
                    RETURN related
                    UNION
                    WITH r
                    MATCH (related:Rule)-[:EXCEPTION_TO|OVERRIDES*1..{depth}]->(r)
                    RETURN related
                }}
                RETURN DISTINCT related
                """,
                ids=rule_ids,
            )
            return [self._row_to_rule(dict(record["related"])) for record in result]
