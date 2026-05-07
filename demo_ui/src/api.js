// API_BASE is set via VITE_API_BASE_URL env var.
// - Development: leave empty; Vite dev-server proxy forwards /api/* → localhost:8000
// - Production: empty string (same-origin — FastAPI serves both API and frontend)
// - Override: set VITE_API_BASE_URL=http://custom-host:8000 for external backends
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/api/health`)
  if (!r.ok) throw new Error('API offline')
  return r.json()
}

export async function fetchScenarios() {
  const r = await fetch(`${API_BASE}/api/scenarios`)
  if (!r.ok) throw new Error('Failed to load scenarios')
  return r.json()
}

export async function runAgent(payload) {
  const r = await fetch(`${API_BASE}/api/run-agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${r.status}`)
  }
  return r.json()
}
