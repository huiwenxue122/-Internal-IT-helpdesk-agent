"""
ASGI entry for deployments using:

    uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

The canonical FastAPI implementation is defined in demo_api.app; this module
exists so render / container platforms can prefer a shorter module path without
changing application behaviour.

Importing ``app.main`` does not initialise ChromaDB, embeddings, Neo4j, or the
LangGraph — those are lazily compiled on first ``run_agent`` / ``POST /run-agent``.
"""

from demo_api.app import app

__all__ = ["app"]
