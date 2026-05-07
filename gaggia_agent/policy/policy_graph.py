from __future__ import annotations

from gaggia_agent.policy.high_risk_rules import HIGH_RISK_RULES
from gaggia_agent.policy.in_memory_graph import InMemoryPolicyGraph
from gaggia_agent.policy.neo4j_graph import Neo4jPolicyGraph


def get_policy_graph(prefer_neo4j: bool = True):
    """
    Return a policy graph backed by Neo4j when credentials are present and the
    connection succeeds; otherwise fall back to the in-memory implementation.

    The returned object satisfies the same interface as both Neo4jPolicyGraph
    and InMemoryPolicyGraph.
    """
    graph, _ = get_policy_graph_with_metadata(prefer_neo4j=prefer_neo4j)
    return graph


def get_policy_graph_with_metadata(prefer_neo4j: bool = True) -> tuple[object, dict]:
    """
    Return (graph, metadata) where metadata describes the active backend.

    metadata keys:
      graph_backend  : "neo4j" | "in_memory"
      neo4j_available: bool
      rules_loaded   : int
    """
    if prefer_neo4j:
        graph = Neo4jPolicyGraph()
        if graph.available():
            graph.load_rules(HIGH_RISK_RULES)
            return graph, {
                "graph_backend": "neo4j",
                "neo4j_available": True,
                "rules_loaded": len(HIGH_RISK_RULES),
            }
        graph.close()

    mem_graph = InMemoryPolicyGraph(rules=HIGH_RISK_RULES)
    return mem_graph, {
        "graph_backend": "in_memory",
        "neo4j_available": False,
        "rules_loaded": len(HIGH_RISK_RULES),
    }
