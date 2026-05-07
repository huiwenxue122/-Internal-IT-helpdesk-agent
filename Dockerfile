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

# Build the in-memory policy index on every cold start, then launch the server.
# This ensures ChromaDB (or its lexical fallback) is ready before the first request.
# CHROMA_PERSIST_PATH can be set to /tmp/chroma_db on platforms with ephemeral disks.
CMD ["sh", "-c", "python scripts/build_policy_index.py && uvicorn demo_api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
