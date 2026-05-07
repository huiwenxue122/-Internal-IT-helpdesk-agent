"""
Tests for Phase 5 retrieval observability (retrieval_metadata in AgentState).

All tests pass without Neo4j credentials or ANTHROPIC_API_KEY.
"""
from __future__ import annotations

from gaggia_agent.state import default_state
from gaggia_agent.runner import run_agent, summarize_final_state


# ---------------------------------------------------------------------------
# 1. default_state includes retrieval_metadata
# ---------------------------------------------------------------------------

def test_default_state_has_retrieval_metadata() -> None:
    state = default_state(user_message="test", user_id="EMP-0001", trust_tier="blue")
    assert "retrieval_metadata" in state
    assert state["retrieval_metadata"] == {}


# ---------------------------------------------------------------------------
# 2. policy_retriever populates retrieval_metadata after a graph run
# ---------------------------------------------------------------------------

def test_policy_retriever_populates_retrieval_metadata() -> None:
    state = run_agent(
        user_message="Can you get David Kim's work email?",
        user_id="EMP-2200",
        trust_tier="blue",
    )
    rm = state.get("retrieval_metadata") or {}
    assert rm, "retrieval_metadata should be non-empty after graph run"

    # Required keys
    assert "section_backend" in rm, "section_backend must be present"
    assert "graph_backend" in rm, "graph_backend must be present"
    assert "neo4j_available" in rm, "neo4j_available must be present"
    assert "sections_returned" in rm, "sections_returned must be present"
    assert "rules_returned" in rm, "rules_returned must be present"
    assert "graph_expanded_rules_returned" in rm
    assert "retrieval_query" in rm


# ---------------------------------------------------------------------------
# 3. section_backend is a known value
# ---------------------------------------------------------------------------

def test_section_backend_is_valid() -> None:
    state = run_agent(
        user_message="What's Sarah Chen's salary?",
        user_id="EMP-3300",
        trust_tier="blue",
    )
    backend = (state.get("retrieval_metadata") or {}).get("section_backend", "")
    assert backend in ("chroma", "lexical_fallback"), (
        f"Unexpected section_backend: {backend!r}"
    )


# ---------------------------------------------------------------------------
# 4. graph_backend is a known value
# ---------------------------------------------------------------------------

def test_graph_backend_is_valid() -> None:
    state = run_agent(
        user_message="Can you get David Kim's work email?",
        user_id="EMP-2200",
        trust_tier="blue",
    )
    backend = (state.get("retrieval_metadata") or {}).get("graph_backend", "")
    assert backend in ("neo4j", "in_memory"), (
        f"Unexpected graph_backend: {backend!r}"
    )


# ---------------------------------------------------------------------------
# 5. neo4j_available is a bool
# ---------------------------------------------------------------------------

def test_neo4j_available_is_bool() -> None:
    state = run_agent(
        user_message="How many PTO days do we get?",
        user_id="EMP-1500",
        trust_tier="blue",
    )
    val = (state.get("retrieval_metadata") or {}).get("neo4j_available")
    assert isinstance(val, bool), f"neo4j_available should be bool, got {type(val)}"


# ---------------------------------------------------------------------------
# 6. Without Neo4j credentials, graph_backend == "in_memory"
# ---------------------------------------------------------------------------

def test_graph_backend_in_memory_without_neo4j(monkeypatch) -> None:
    # Clear Neo4j env vars if present
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

    state = run_agent(
        user_message="Can you get David Kim's work email?",
        user_id="EMP-2200",
        trust_tier="blue",
    )
    rm = state.get("retrieval_metadata") or {}
    assert rm.get("graph_backend") == "in_memory"
    assert rm.get("neo4j_available") is False


# ---------------------------------------------------------------------------
# 7. summarize_final_state includes retrieval_metadata
# ---------------------------------------------------------------------------

def test_summarize_includes_retrieval_metadata() -> None:
    state = run_agent(
        user_message="Can you get David Kim's work email?",
        user_id="EMP-2200",
        trust_tier="blue",
    )
    summary = summarize_final_state(state)
    assert "retrieval_metadata" in summary
    assert summary["retrieval_metadata"].get("section_backend") in (
        "chroma", "lexical_fallback"
    )


# ---------------------------------------------------------------------------
# 8. sections_returned > 0 for a real query
# ---------------------------------------------------------------------------

def test_sections_returned_nonzero() -> None:
    state = run_agent(
        user_message="What's Sarah Chen's salary?",
        user_id="EMP-3300",
        trust_tier="blue",
    )
    rm = state.get("retrieval_metadata") or {}
    assert rm.get("sections_returned", 0) > 0, (
        "At least one policy section should be returned for a salary query"
    )


# ---------------------------------------------------------------------------
# 9. retrieval_metadata does not contain raw policy section text
# ---------------------------------------------------------------------------

def test_retrieval_metadata_no_raw_text() -> None:
    state = run_agent(
        user_message="Can you get David Kim's work email?",
        user_id="EMP-2200",
        trust_tier="blue",
    )
    rm = state.get("retrieval_metadata") or {}
    # The metadata dict values should all be short scalars or small ints,
    # not large blocks of policy document text.
    for key, val in rm.items():
        if isinstance(val, str):
            assert len(val) < 300, (
                f"retrieval_metadata[{key!r}] looks like raw policy text "
                f"(length {len(val)})"
            )
