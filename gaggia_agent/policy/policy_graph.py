from __future__ import annotations

import os

from gaggia_agent.policy.high_risk_rules import HIGH_RISK_RULES
from gaggia_agent.policy.in_memory_graph import InMemoryPolicyGraph

# ---------------------------------------------------------------------------
# Backend selection
#
# POLICY_GRAPH_BACKEND=memory  (default, Render-safe)
#   In-process rule graph.  No network connection, no external credentials.
#
# POLICY_GRAPH_BACKEND=neo4j
#   Neo4j AuraDB.  Requires NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD.
#   If the connection fails, falls back to in-memory automatically.
# ---------------------------------------------------------------------------

_GRAPH_BACKEND: str = os.getenv("POLICY_GRAPH_BACKEND", "memory").lower()


def get_policy_graph(prefer_neo4j: bool | None = None):
    """
    Return a policy graph.  Backend is controlled by POLICY_GRAPH_BACKEND env var.

    prefer_neo4j is accepted for backwards-compatibility but is overridden by
    the env var when POLICY_GRAPH_BACKEND is explicitly set.
    """
    graph, _ = get_policy_graph_with_metadata(prefer_neo4j=prefer_neo4j)
    return graph


def get_policy_graph_with_metadata(
    prefer_neo4j: bool | None = None,
) -> tuple[object, dict]:
    """
    Return (graph, metadata) where metadata describes the active backend.

    metadata keys:
      graph_backend  : "neo4j" | "in_memory"
      neo4j_available: bool
      rules_loaded   : int
    """
    # Explicit opt-in only (Render default POLICY_GRAPH_BACKEND=memory is safe).
    # prefer_neo4j kwarg ignored — use POLICY_GRAPH_BACKEND=neo4j instead.
    if _GRAPH_BACKEND == "neo4j":
        from gaggia_agent.policy.neo4j_graph import Neo4jPolicyGraph  # lazy import
        graph = Neo4jPolicyGraph()
        if graph.available():
            graph.load_rules(HIGH_RISK_RULES)
            return graph, {
                "graph_backend": "neo4j",
                "neo4j_available": True,
                "rules_loaded": len(HIGH_RISK_RULES),
            }
        graph.close()
        # Fall through to in-memory on connection failure

    mem_graph = InMemoryPolicyGraph(rules=HIGH_RISK_RULES)
    return mem_graph, {
        "graph_backend": "in_memory",
        "neo4j_available": False,
        "rules_loaded": len(HIGH_RISK_RULES),
    }
