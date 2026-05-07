from __future__ import annotations

import os

from gaggia_agent.policy.chroma_index import (
    build_lexical_only,
    hydrate_lexical_cache_from_policy,
    query_chroma_with_metadata,
    require_runtime_chroma_index,
    set_using_lexical,
    _lexical_index,
)
from gaggia_agent.policy.policy_graph import get_policy_graph_with_metadata
from gaggia_agent.state import AgentState

# ---------------------------------------------------------------------------
# Backend selection
#
# RETRIEVER_BACKEND=keyword  (default, Render-safe)
#   Uses a pure-Python keyword/lexical index.  No chromadb, no ONNX model.
#
# RETRIEVER_BACKEND=chroma
#   Uses ChromaDB with sentence-transformer embeddings.  Requires the index
#   to have been built offline via  python scripts/build_policy_index.py .
#   If the index is missing, raises a clear error rather than building it
#   during web startup (which would exceed memory on small instances).
# ---------------------------------------------------------------------------

_RETRIEVER_BACKEND: str = os.getenv("RETRIEVER_BACKEND", "keyword").lower()


def _ensure_section_index() -> None:
    """Populate the in-process section index if empty."""
    if _lexical_index._docs:
        return  # already loaded
    if _RETRIEVER_BACKEND == "chroma":
        require_runtime_chroma_index()
        set_using_lexical(False)
        hydrate_lexical_cache_from_policy()
    else:
        # Keyword mode (default): load the lexical index only.
        build_lexical_only()


def policy_retriever(state: AgentState) -> AgentState:
    """
    Populate state with a Policy Evidence Bundle.

    Section retrieval backend is controlled by the RETRIEVER_BACKEND env var:
      keyword (default) — pure Python lexical matching, Render-safe
      chroma            — ChromaDB with sentence-transformer embeddings

    Policy graph backend is controlled by POLICY_GRAPH_BACKEND:
      memory (default) — in-memory rule graph, no Neo4j connection
      neo4j            — Neo4j AuraDB (requires NEO4J_URI/USERNAME/PASSWORD)

    Populates state["retrieval_metadata"] with backend observability info.
    """
    # -----------------------------------------------------------------------
    # 1. Build retrieval query (compact, no raw sensitive values)
    # -----------------------------------------------------------------------
    query_parts: list[str] = []

    if state.get("user_message"):
        query_parts.append(state["user_message"])
    if state.get("intent"):
        query_parts.append(state["intent"])
    if state.get("requested_fields"):
        query_parts.extend(state["requested_fields"])
    if state.get("candidate_tools"):
        query_parts.extend(state["candidate_tools"])
    if state.get("risk_level"):
        query_parts.append(state["risk_level"])
    if state.get("adversarial_signals"):
        query_parts.extend(state["adversarial_signals"])

    query = " ".join(query_parts)

    # -----------------------------------------------------------------------
    # 2. Section retrieval (keyword or Chroma)
    # -----------------------------------------------------------------------
    _ensure_section_index()
    raw_sections, section_meta = query_chroma_with_metadata(
        query,
        k=6,
        allow_auto_build=(_RETRIEVER_BACKEND != "chroma"),
    )

    # Annotate metadata with active backend name
    section_meta.setdefault("section_backend", _RETRIEVER_BACKEND)
    retrieved_sections: list[dict] = []
    seen_section_ids: set[str] = set()
    for sec in raw_sections:
        sid = sec.get("section_id", "")
        if sid and sid not in seen_section_ids:
            retrieved_sections.append(sec)
            seen_section_ids.add(sid)
    state["retrieved_sections"] = retrieved_sections

    # -----------------------------------------------------------------------
    # 3. Policy graph rule retrieval
    # -----------------------------------------------------------------------
    graph, graph_meta = get_policy_graph_with_metadata()

    direct_rules = graph.find_rules_for_query_context(
        intent=state.get("intent", ""),
        requested_fields=state.get("requested_fields", []),
        candidate_tools=state.get("candidate_tools", []),
        risk_level=state.get("risk_level", ""),
        trust_tier=state.get("trust_tier", ""),
        user_message=state.get("user_message", ""),
        adversarial_signals=state.get("adversarial_signals", []),
    )

    seen_rule_ids: set[str] = set()
    retrieved_rules: list[dict] = []
    for rule in direct_rules:
        if rule.rule_id not in seen_rule_ids:
            retrieved_rules.append(rule.to_dict())
            seen_rule_ids.add(rule.rule_id)
    state["retrieved_rules"] = retrieved_rules

    # -----------------------------------------------------------------------
    # 4. Expand related rules through graph relationships
    # -----------------------------------------------------------------------
    seed_ids = list(seen_rule_ids)
    expanded_rules = graph.expand_related_rules(seed_ids, depth=2)

    graph_expanded: list[dict] = []
    for rule in expanded_rules:
        if rule.rule_id not in seen_rule_ids:
            graph_expanded.append(rule.to_dict())
            seen_rule_ids.add(rule.rule_id)
    state["graph_expanded_rules"] = graph_expanded

    # -----------------------------------------------------------------------
    # 5. Populate retrieval_metadata (observability — no raw policy text)
    # -----------------------------------------------------------------------
    state["retrieval_metadata"] = {
        # Section retrieval backend
        "section_backend": section_meta.get("section_backend", "unknown"),
        **({
            "collection": section_meta["collection"],
            "chroma_path": section_meta.get("chroma_path", ""),
        } if section_meta.get("section_backend") == "chroma" else {
            "fallback_reason": section_meta.get("reason", ""),
        }),
        # Graph retrieval backend
        "graph_backend": graph_meta.get("graph_backend", "unknown"),
        "neo4j_available": graph_meta.get("neo4j_available", False),
        "rules_loaded": graph_meta.get("rules_loaded", 0),
        # Counts
        "sections_returned": len(retrieved_sections),
        "rules_returned": len(retrieved_rules),
        "graph_expanded_rules_returned": len(graph_expanded),
        # Compact query string (truncated to avoid bloating state)
        "retrieval_query": query[:200],
    }

    return state
