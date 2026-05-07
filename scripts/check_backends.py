#!/usr/bin/env python3
"""
check_backends.py — print the active backend for every pluggable component.

Usage:
    python scripts/check_backends.py

Checks (in order):
  1. .env loading
  2. LLM provider (Anthropic / fallback)
  3. ChromaDB vs lexical fallback
  4. Neo4j vs in-memory policy graph
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env first so credentials are available.
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

import gaggia_agent._compat  # noqa: F401 — apply langchain globals patch


def _check_llm() -> None:
    from gaggia_agent.llm.client import LLMClient
    client = LLMClient()
    if client.available():
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        print(f"LLM provider:   anthropic")
        print(f"LLM model:      {model}")
    else:
        print(f"LLM provider:   deterministic_fallback  (ANTHROPIC_API_KEY not set or invalid)")
        print(f"LLM model:      (none)")


def _check_chroma() -> None:
    from gaggia_agent.policy.chroma_index import query_chroma_with_metadata, build_chroma_index, _lexical_index
    chroma_path = os.environ.get("CHROMA_PERSIST_PATH", "./chroma_db")
    path_exists = os.path.isdir(chroma_path)

    # Ensure the index is initialised.
    if not _lexical_index._docs:
        build_chroma_index()

    _, meta = query_chroma_with_metadata("test query", k=1)
    backend = meta.get("section_backend", "unknown")
    print(f"Section backend: {backend}")
    if backend == "chroma":
        print(f"Chroma path:    {meta.get('chroma_path', chroma_path)}")
        print(f"Collection:     {meta.get('collection', 'gaggia_policy_sections')}")
    else:
        print(f"Chroma path:    {chroma_path}  (exists={path_exists})")
        reason = meta.get("reason", "")
        if reason:
            print(f"Fallback reason:{reason[:120]}")
    print(f"Chroma dir exists: {path_exists}")


def _check_graph() -> None:
    from gaggia_agent.policy.policy_graph import get_policy_graph_with_metadata
    _, meta = get_policy_graph_with_metadata(prefer_neo4j=True)
    print(f"Graph backend:  {meta.get('graph_backend', 'unknown')}")
    print(f"Neo4j available:{meta.get('neo4j_available', False)}")
    print(f"Rules loaded:   {meta.get('rules_loaded', 0)}")


def _check_langsmith() -> None:
    tracing = os.environ.get("LANGCHAIN_TRACING_V2", "").lower()
    key_set = bool(os.environ.get("LANGCHAIN_API_KEY", "").strip())
    project = os.environ.get("LANGCHAIN_PROJECT", "(default)")
    print(f"LangSmith tracing: {'enabled' if tracing == 'true' else 'disabled'}")
    if tracing == "true":
        print(f"LangSmith key set: {key_set}")
        print(f"LangSmith project: {project}")


def main() -> None:
    print()
    print("=" * 48)
    print("  GaggiaAgent — Backend Status")
    print("=" * 48)

    print()
    print("── LLM ──────────────────────────────────────────")
    _check_llm()

    print()
    print("── Policy Section Retrieval ─────────────────────")
    _check_chroma()

    print()
    print("── Policy Rule Graph ────────────────────────────")
    _check_graph()

    print()
    print("── Observability ────────────────────────────────")
    _check_langsmith()

    print()
    print("=" * 48)


if __name__ == "__main__":
    main()
