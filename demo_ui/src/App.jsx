import { useState, useEffect } from 'react'
import { fetchHealth, fetchScenarios, runAgent } from './api'
import { findRunAsForSuggested, resolveEffective } from './runAs'
import ScenarioPicker from './components/ScenarioPicker'
import RunAsSelector from './components/RunAsSelector'
import AdvancedOverrides from './components/AdvancedOverrides'
import EffectiveRequest from './components/EffectiveRequest'
import ResponseCard from './components/ResponseCard'
import TracePanel from './components/TracePanel'
import ComparePanel from './components/ComparePanel'

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  // Scenarios from API
  const [scenarios, setScenarios] = useState([])
  const [selectedScenarioId, setSelectedScenarioId] = useState(null)
  const [message, setMessage] = useState('')

  // ── Primary "Run As" identity ────────────────────────────────────────────
  // Mental model: Scenario = what is asked, Run As = who is asking.
  // Changing a scenario NEVER changes runAsId or overrides.
  const [runAsId, setRunAsId] = useState('blue_jessica_park')

  // ── Advanced overrides (null = not overridden, use Run As defaults) ──────
  const [advTier,      setAdvTier]      = useState(null)
  const [advUserId,    setAdvUserId]    = useState(null)
  const [advProfileId, setAdvProfileId] = useState(null)

  // Derived effective values
  const { tier: effectiveTier, userId: effectiveUserId,
          profileId: effectiveProfileId, profile: effectiveProfile } =
    resolveEffective(runAsId, advTier, advUserId, advProfileId)

  const advancedActive = !!(advTier || advUserId !== null || advProfileId) || runAsId === 'custom'

  // Run results
  const [loading,        setLoading]        = useState(false)
  const [result,         setResult]         = useState(null)
  const [error,          setError]          = useState(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareResults, setCompareResults] = useState(null)

  // API health
  const [health,     setHealth]     = useState(null)
  const [apiOffline, setApiOffline] = useState(false)

  // ── Init ────────────────────────────────────────────────────────────────

  useEffect(() => {
    fetchHealth()
      .then(h => { setHealth(h); setApiOffline(false) })
      .catch(() => setApiOffline(true))
    fetchScenarios().then(setScenarios).catch(() => {})
  }, [])

  // ── Scenario selection — ONLY updates the message ───────────────────────
  // runAsId and all overrides are untouched.

  const handleScenarioSelect = (scenario) => {
    setSelectedScenarioId(scenario.id)
    setMessage(scenario.message)
    setResult(null)
    setCompareResults(null)
    setError(null)
  }

  // ── "Use suggested context" — sets Run As to scenario's suggestion ───────
  // Only called when user explicitly clicks the button in ScenarioPicker.

  const handleApplySuggested = (scenario) => {
    if (!scenario) return
    const opt = findRunAsForSuggested(scenario.suggested_profile_id, scenario.suggested_trust_tier)
    if (opt) {
      setRunAsId(opt.id)
      setAdvTier(null)
      setAdvUserId(null)
      setAdvProfileId(null)
    }
  }

  // ── Run As selector change — clears overrides (except for Custom) ────────

  const handleRunAsChange = (id) => {
    setRunAsId(id)
    if (id !== 'custom') {
      setAdvTier(null)
      setAdvUserId(null)
      setAdvProfileId(null)
    }
  }

  // ── Reset advanced overrides ─────────────────────────────────────────────

  const handleResetAdvanced = () => {
    setAdvTier(null)
    setAdvUserId(null)
    setAdvProfileId(null)
    if (runAsId === 'custom') setRunAsId('blue_jessica_park')
  }

  // ── Build payload ────────────────────────────────────────────────────────

  const payload = (tier) => ({
    message,
    trust_tier: tier || effectiveTier,
    user_id: effectiveUserId,
    requester_profile: effectiveProfile,
  })

  // ── Single run ───────────────────────────────────────────────────────────

  const handleRun = async () => {
    if (!message.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setCompareResults(null)
    try {
      setResult(await runAgent(payload()))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Compare: same message + profile, three trust tiers ──────────────────

  const handleCompare = async () => {
    if (!message.trim()) return
    setCompareLoading(true)
    setError(null)
    setResult(null)
    setCompareResults(null)
    try {
      const [blueRes, greyRes, redRes] = await Promise.all([
        runAgent(payload('blue')).catch(e => ({ error: e.message })),
        runAgent(payload('grey')).catch(e => ({ error: e.message })),
        runAgent(payload('red')).catch(e => ({ error: e.message })),
      ])
      setCompareResults({ blue: blueRes, grey: greyRes, red: redRes })
    } catch (e) {
      setError(e.message)
    } finally {
      setCompareLoading(false)
    }
  }

  // ── Derived: does current context match scenario suggestion? ─────────────

  const selectedScenario = scenarios.find(s => s.id === selectedScenarioId)
  const suggestedRunAs = selectedScenario
    ? findRunAsForSuggested(selectedScenario.suggested_profile_id, selectedScenario.suggested_trust_tier)
    : null
  const contextDiffers = !!(suggestedRunAs && runAsId !== suggestedRunAs.id) || advancedActive

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="app">
      <header className="app-header">
        <h1><span>🛡️</span>GaggiaAgent Policy Console</h1>
        <div className="header-meta">
          {health && <span className="health-badge">{health.llm_mode} · {health.version}</span>}
          <span className={`api-status ${apiOffline ? 'err' : 'ok'}`}>
            {apiOffline ? '● API offline' : '● API online'}
          </span>
        </div>
      </header>

      <main className="app-main">
        {/* ── LEFT SIDEBAR ── */}
        <aside className="sidebar">

          {/* 1. Scenario selector */}
          <ScenarioPicker
            scenarios={scenarios}
            selectedId={selectedScenarioId}
            onSelect={handleScenarioSelect}
            onApplySuggested={handleApplySuggested}
          />

          {/* 2. Run As — primary identity */}
          <RunAsSelector
            runAsId={runAsId}
            onChange={handleRunAsChange}
          />

          {/* 3. Message + actions */}
          <div className="sidebar-section sidebar-message">
            <div className="sidebar-label">Message</div>
            <div className="form-group">
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder="Type your helpdesk request, or select a template above…"
                rows={5}
              />
            </div>

            <EffectiveRequest
              runAsId={runAsId}
              effectiveTier={effectiveTier}
              effectiveUserId={effectiveUserId}
              effectiveProfile={effectiveProfile}
              message={message}
              selectedScenario={selectedScenario}
              contextDiffers={contextDiffers}
              advancedActive={advancedActive}
            />

            <div className="action-btns">
              <button
                className="run-btn"
                onClick={handleRun}
                disabled={loading || compareLoading || !message.trim()}
              >
                {loading ? '⏳ Running…' : '▶ Run Agent'}
              </button>
              <button
                className="compare-btn"
                onClick={handleCompare}
                disabled={loading || compareLoading || !message.trim()}
                title="Run the same message under Blue, Grey, and Red with the current profile"
              >
                {compareLoading ? '⏳ Comparing…' : '⚖️ Compare Blue / Grey / Red'}
              </button>
            </div>
          </div>

          {/* 4. Advanced Overrides — collapsed by default */}
          <AdvancedOverrides
            effectiveTier={effectiveTier}
            effectiveUserId={effectiveUserId}
            effectiveProfileId={effectiveProfileId}
            advTier={advTier}       setAdvTier={setAdvTier}
            advUserId={advUserId}   setAdvUserId={setAdvUserId}
            advProfileId={advProfileId} setAdvProfileId={setAdvProfileId}
            advancedActive={advancedActive}
            onReset={handleResetAdvanced}
          />
        </aside>

        {/* ── RIGHT RESULTS ── */}
        <section className="results">
          {error && <div className="error-banner">⚠️ {error}</div>}

          {!result && !compareResults && !loading && !compareLoading && !error && (
            <div className="placeholder">
              <p>
                Pick an <strong>Official Test Scenario</strong>, set{' '}
                <strong>Run As</strong>, then click{' '}
                <strong>Run Agent</strong> — or{' '}
                <strong>Compare Blue / Grey / Red</strong> to see how trust
                tier changes the outcome.
              </p>
            </div>
          )}

          {(loading || compareLoading) && (
            <div className="loading">
              <div className="spinner" />
              {compareLoading ? 'Running under Blue, Grey, and Red…' : 'Running LangGraph agent…'}
            </div>
          )}

          {result && !loading && (
            <>
              <ResponseCard result={result} />
              <TracePanel result={result} />
            </>
          )}

          {compareResults && !compareLoading && (
            <ComparePanel results={compareResults} />
          )}
        </section>
      </main>
    </div>
  )
}
