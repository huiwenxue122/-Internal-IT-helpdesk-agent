import { useState } from 'react'
import PolicyEvidence from './PolicyEvidence'
import ToolTrace from './ToolTrace'

const TABS = [
  { id: 'router',   label: '🔀 Router' },
  { id: 'evidence', label: '📚 Policy Evidence' },
  { id: 'conflicts', label: '⚠️ Conflicts' },
  { id: 'tools',    label: '🔧 Tool Safety' },
  { id: 'filter',   label: '🛡️ Output Filter' },
  { id: 'backend',  label: '⚙️ Backend' },
]

function RouterPane({ result }) {
  const risks = { high: 'risk-high', medium: 'risk-medium', low: 'risk-low' }
  const riskClass = risks[result.risk_level] || 'risk-unknown'
  return (
    <div>
      <div className="trace-row">
        <div className="trace-key">Intent</div>
        <div className="trace-val">
          <span className="chip">{result.intent || '—'}</span>
        </div>
      </div>
      <div className="trace-row">
        <div className="trace-key">Requested Fields</div>
        <div className="trace-val">
          {result.requested_fields?.length > 0
            ? <div className="chips">{result.requested_fields.map(f => <span key={f} className="chip">{f}</span>)}</div>
            : <span className="empty-state">none</span>}
        </div>
      </div>
      <div className="trace-row">
        <div className="trace-key">Candidate Tools</div>
        <div className="trace-val">
          {result.candidate_tools?.length > 0
            ? <div className="chips">{result.candidate_tools.map(t => <span key={t} className="chip chip-purple">{t}</span>)}</div>
            : <span className="empty-state">none</span>}
        </div>
      </div>
      <div className="trace-row">
        <div className="trace-key">Risk Level</div>
        <div className="trace-val">
          <span className={`risk-badge ${riskClass}`}>{result.risk_level || 'unknown'}</span>
        </div>
      </div>
      <div className="trace-row">
        <div className="trace-key">Adversarial Signals</div>
        <div className="trace-val">
          {result.adversarial_signals?.length > 0
            ? <div className="chips">{result.adversarial_signals.map(s => <span key={s} className="chip chip-red">{s}</span>)}</div>
            : <span style={{ color: 'var(--allow)', fontSize: '12px' }}>✅ None detected</span>}
        </div>
      </div>
    </div>
  )
}

function ConflictsPane({ result }) {
  const conflicts = result.conflicts_detected || []
  if (!conflicts.length) {
    return <div className="empty-state">No policy conflicts detected.</div>
  }
  return (
    <div>
      {conflicts.map((c, i) => (
        <div key={i} className="conflict-card">
          <div className="conflict-type">{c.conflict_type || c.type || 'conflict'}</div>
          {c.rule_ids && (
            <div className="chips">
              {c.rule_ids.map(r => <span key={r} className="chip chip-yellow">{r}</span>)}
            </div>
          )}
          {c.resolution_hint && (
            <div className="conflict-hint">💡 {c.resolution_hint}</div>
          )}
        </div>
      ))}
    </div>
  )
}

function OutputFilterPane({ result }) {
  const hasOutputs = Object.keys(result.filtered_tool_outputs || {}).length > 0
  return (
    <div>
      <div className="trace-section-title">
        Redacted Fields ({result.redacted_fields?.length ?? 0})
      </div>
      {result.redacted_fields?.length > 0 ? (
        <div className="chips">
          {result.redacted_fields.map(f => <span key={f} className="chip chip-red">{f}</span>)}
        </div>
      ) : <div className="empty-state">No fields redacted.</div>}

      <div className="trace-section-title">Filtered Tool Outputs</div>
      {hasOutputs ? (
        <pre className="json-pre">{JSON.stringify(result.filtered_tool_outputs, null, 2)}</pre>
      ) : <div className="empty-state">No filtered outputs available.</div>}
    </div>
  )
}

const TIER_COLOR = { blue: '#3b82f6', grey: '#64748b', red: '#ef4444' }

function BackendPane({ result }) {
  const m = result.retrieval_metadata || {}
  const sub = result.submitted_input || {}
  const log = result.decision_log_summary || {}
  const items = [
    { label: 'Section Backend', value: m.section_backend || '—', ok: m.section_backend === 'chroma' },
    { label: 'Graph Backend', value: m.graph_backend || '—', ok: m.graph_backend === 'neo4j' },
    { label: 'Neo4j Available', value: m.neo4j_available != null ? String(m.neo4j_available) : '—', ok: m.neo4j_available === true },
    { label: 'Rules Loaded', value: m.rules_loaded != null ? String(m.rules_loaded) : '—', ok: true },
    { label: 'Sections Returned', value: m.sections_returned != null ? String(m.sections_returned) : '—', ok: true },
    { label: 'Rules Returned', value: m.rules_returned != null ? String(m.rules_returned) : '—', ok: true },
  ]
  return (
    <div>
      {/* Submitted input — lets the user verify tier/profile actually used */}
      {Object.keys(sub).length > 0 && (
        <>
          <div className="trace-section-title">Submitted Input (verified by backend)</div>
          <div>
            {[
              ['Trust Tier', sub.trust_tier],
              ['User ID', sub.user_id],
              ['Profile Name', sub.requester_profile?.name],
              ['Department', sub.requester_profile?.department],
              ['Is Manager', sub.requester_profile?.is_manager != null ? String(sub.requester_profile.is_manager) : undefined],
              ['Verified', sub.requester_profile?.verified != null ? String(sub.requester_profile.verified) : undefined],
            ].filter(([, v]) => v != null).map(([k, v]) => (
              <div key={k} className="trace-row">
                <div className="trace-key">{k}</div>
                <div className="trace-val" style={{
                  fontSize: 12,
                  fontFamily: k === 'User ID' ? 'var(--mono)' : undefined,
                  color: k === 'Trust Tier' ? TIER_COLOR[v] || 'inherit' : undefined,
                  fontWeight: k === 'Trust Tier' ? 700 : undefined,
                }}>{v}</div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="trace-section-title" style={{ marginTop: 16 }}>Retrieval Backends</div>
      <div className="meta-grid">
        {items.map(item => (
          <div key={item.label} className="meta-item">
            <div className="meta-label">{item.label}</div>
            <div className={`meta-value ${item.ok ? 'meta-ok' : 'meta-warn'}`}>{item.value}</div>
          </div>
        ))}
      </div>

      {m.retrieval_query && (
        <>
          <div className="trace-section-title">Retrieval Query</div>
          <div className="chip" style={{ fontFamily: 'var(--mono)', fontSize: '11px', display: 'inline-block' }}>
            {m.retrieval_query}
          </div>
        </>
      )}

      {Object.keys(log).length > 0 && (
        <>
          <div className="trace-section-title">Decision Log Summary</div>
          <div>
            {Object.entries(log).map(([k, v]) => (
              <div key={k} className="trace-row">
                <div className="trace-key">{k.replace(/_/g, ' ')}</div>
                <div className="trace-val" style={{ fontSize: '12px', fontFamily: typeof v === 'string' && v.startsWith('REQ-') ? 'var(--mono)' : undefined }}>
                  {Array.isArray(v) ? (
                    v.length > 0
                      ? <div className="chips">{v.map((x, i) => <span key={i} className="chip">{x}</span>)}</div>
                      : <span className="empty-state">[]</span>
                  ) : String(v ?? '—')}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function TracePanel({ result }) {
  const [activeTab, setActiveTab] = useState('router')

  return (
    <div className="card">
      <div className="trace-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`trace-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="trace-pane">
        {activeTab === 'router'    && <RouterPane result={result} />}
        {activeTab === 'evidence'  && <PolicyEvidence result={result} />}
        {activeTab === 'conflicts' && <ConflictsPane result={result} />}
        {activeTab === 'tools'     && <ToolTrace result={result} />}
        {activeTab === 'filter'    && <OutputFilterPane result={result} />}
        {activeTab === 'backend'   && <BackendPane result={result} />}
      </div>
    </div>
  )
}
