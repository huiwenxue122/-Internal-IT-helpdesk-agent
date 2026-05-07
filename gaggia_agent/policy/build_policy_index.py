from __future__ import annotations

from gaggia_agent.policy.chroma_index import build_chroma_index, _using_lexical
from gaggia_agent.policy.high_risk_rules import HIGH_RISK_RULES
from gaggia_agent.policy.policy_graph import get_policy_graph


def build_all_policy_indexes(reset: bool = False) -> dict:
    """
    Build or rebuild all policy indexes.

    Returns a summary dict:
        {
            "sections_indexed": int,
            "rules_loaded": int,
            "graph_backend": "neo4j" | "in_memory",
        }
    """
    sections_indexed = build_chroma_index(reset=reset)

    graph = get_policy_graph(prefer_neo4j=True)
    graph_backend = "neo4j" if type(graph).__name__ == "Neo4jPolicyGraph" else "in_memory"

    return {
        "sections_indexed": sections_indexed,
        "rules_loaded": len(HIGH_RISK_RULES),
        "graph_backend": graph_backend,
    }
