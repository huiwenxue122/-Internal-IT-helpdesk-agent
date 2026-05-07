# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Build the React frontend
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS frontend

WORKDIR /app/demo_ui

# Install dependencies first for layer caching
COPY demo_ui/package*.json ./
RUN npm install

# Copy source and build
COPY demo_ui/ .
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Python backend + bundled frontend assets
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY . .

# Pull in the compiled React assets from stage 1
COPY --from=frontend /app/demo_ui/dist ./demo_ui/dist

EXPOSE 8000

# Default: start the server directly.
# RETRIEVER_BACKEND=keyword (the default) uses a pure-Python lexical index that
# is built on the first request — no Chroma, no ONNX download, memory-safe.
#
# For local full mode with Chroma embeddings, override at build/run time:
#   docker run --env RETRIEVER_BACKEND=chroma --env-file .env ...
#   (and run  python scripts/build_policy_index.py  first to populate the index)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
