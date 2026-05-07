"""
ChromaDB policy index with a pure-Python lexical fallback.

The lexical fallback activates automatically when:
  - chromadb is not installed, or
  - the embedding model cannot be loaded (offline / CI environments).

Function signatures are identical in both paths so callers never branch.
"""

from __future__ import annotations

import os
import re
from typing import Any, List

from gaggia_agent.policy.section_parser import parse_policy_markdown

_DEFAULT_PERSIST_PATH = os.environ.get("CHROMA_PERSIST_PATH", "./chroma_db")
_COLLECTION_NAME = "gaggia_policy_sections"


# ---------------------------------------------------------------------------
# Lexical fallback
# ---------------------------------------------------------------------------

class _LexicalIndex:
    """Simple keyword-overlap retriever used when ChromaDB is unavailable."""

    def __init__(self) -> None:
        self._docs: list[dict] = []

    def reset(self) -> None:
        self._docs = []

    def add_sections(self, sections: list) -> None:
        self._docs = [
            {
                "section_id": s.section_id,
                "title": s.title,
                "domain": s.domain,
                "modality": s.modality or "",
                "tags": ",".join(s.tags),
                "content": s.content,
            }
            for s in sections
        ]

    def query(self, query: str, k: int = 6) -> list[dict]:
        tokens = set(re.findall(r"\w+", query.lower()))
        scored: list[tuple[float, dict]] = []
        for doc in self._docs:
            doc_tokens = set(re.findall(r"\w+", doc["content"].lower()))
            overlap = len(tokens & doc_tokens)
            score = overlap / (len(tokens) + 1)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {**doc, "distance": max(0.0, 1.0 - score)}
            for score, doc in scored[:k]
        ]


# Module-level fallback instance (used when chromadb is absent/broken)
_lexical_index: _LexicalIndex = _LexicalIndex()
_using_lexical: bool = False


# ---------------------------------------------------------------------------
# ChromaDB helpers
# ---------------------------------------------------------------------------

def _try_get_chroma_client(persist_path: str) -> Any:
    import chromadb  # type: ignore
    return chromadb.PersistentClient(path=persist_path)


def _try_get_collection(client: Any, reset: bool) -> Any:
    import chromadb  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore

    ef = embedding_functions.DefaultEmbeddingFunction()

    if reset:
        try:
            client.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass

    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_chroma_client(persist_path: str | None = None) -> Any:
    path = persist_path or _DEFAULT_PERSIST_PATH
    return _try_get_chroma_client(path)


def build_chroma_index(
    policy_path: str | None = None,
    persist_path: str | None = None,
    reset: bool = False,
) -> int:
    global _using_lexical

    from gaggia_agent.policy.section_parser import _POLICY_PATH  # type: ignore

    path = policy_path or _POLICY_PATH
    sections = parse_policy_markdown(path)

    try:
        client = _try_get_chroma_client(persist_path or _DEFAULT_PERSIST_PATH)
        collection = _try_get_collection(client, reset=reset)

        ids = [s.section_id for s in sections]
        documents = [s.content for s in sections]
        metadatas = [
            {
                "section_id": s.section_id,
                "title": s.title,
                "domain": s.domain,
                "modality": s.modality or "",
                "tags": ",".join(s.tags),
            }
            for s in sections
        ]

        # Upsert in batches to avoid size limits
        batch_size = 50
        for i in range(0, len(ids), batch_size):
            collection.upsert(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

        _using_lexical = False
        # Keep lexical index in sync for query_chroma fallback awareness
        _lexical_index.add_sections(sections)
        return len(sections)

    except Exception:
        # ChromaDB unavailable or embedding failed — use lexical fallback
        _using_lexical = True
        _lexical_index.add_sections(sections)
        return len(sections)


def query_chroma(
    query: str,
    k: int = 6,
    persist_path: str | None = None,
) -> List[dict]:
    """Query the section index; returns results only (no backend metadata)."""
    results, _ = query_chroma_with_metadata(query, k=k, persist_path=persist_path)
    return results


def query_chroma_with_metadata(
    query: str,
    k: int = 6,
    persist_path: str | None = None,
) -> tuple[List[dict], dict]:
    """
    Query the section index and return (results, backend_metadata).

    backend_metadata keys:
      section_backend : "chroma" | "lexical_fallback"
      collection      : collection name (chroma only)
      chroma_path     : persist path (chroma only)
      reason          : why fallback was used (lexical only)
    """
    global _using_lexical

    path = persist_path or _DEFAULT_PERSIST_PATH

    # If we already know lexical is the backend, short-circuit
    if _using_lexical:
        return _lexical_index.query(query, k=k), {
            "section_backend": "lexical_fallback",
            "reason": "ChromaDB unavailable or embedding failed",
        }

    # Cold start — build index
    if not _lexical_index._docs:
        build_chroma_index(persist_path=path)
        if _using_lexical:
            return _lexical_index.query(query, k=k), {
                "section_backend": "lexical_fallback",
                "reason": "ChromaDB unavailable at index build time",
            }

    try:
        client = _try_get_chroma_client(path)

        import chromadb  # type: ignore
        from chromadb.utils import embedding_functions  # type: ignore

        ef = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=ef,
        )
        results = collection.query(query_texts=[query], n_results=min(k, collection.count()))
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        sections = [
            {
                "section_id": m.get("section_id", ""),
                "title": m.get("title", ""),
                "domain": m.get("domain", ""),
                "modality": m.get("modality", ""),
                "tags": m.get("tags", ""),
                "content": d,
                "distance": dist,
            }
            for d, m, dist in zip(docs, metas, distances)
        ]
        return sections, {
            "section_backend": "chroma",
            "collection": _COLLECTION_NAME,
            "chroma_path": path,
        }

    except Exception as exc:
        _using_lexical = True
        return _lexical_index.query(query, k=k), {
            "section_backend": "lexical_fallback",
            "reason": str(exc)[:120],
        }
