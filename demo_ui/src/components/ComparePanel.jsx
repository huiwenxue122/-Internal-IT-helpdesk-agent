import VerdictBadge from './VerdictBadge'

const TIER_LABEL = { blue: '🔵 Blue', grey: '⚪ Grey', red: '🔴 Red' }

function CompareCard({ tier, result }) {
  if (!result) return (
    <div className="compare-card compare-card-loading">
      <div className="compare-tier">{TIER_LABEL[tier] || tier}</div>
      <div className="empty-state">Running…</div>
    </div>
  )

  if (result.error) return (
    <div className="compare-card compare-card-error">
      <div className="compare-tier">{TIER_LABEL[tier] || tier}</div>
      <div style={{ color: 'var(--deny)', fontSize: 12 }}>Error: {result.error}</div>
    </div>
  )

  return (
    <div className="compare-card">
      <div className="compare-tier-row">
        <span className="compare-tier">{TIER_LABEL[tier] || tier}</span>
        <VerdictBadge verdict={result.verdict} />
      </div>
      <p className="compare-response">{result.response}</p>
      {result.cited_sections?.length > 0 && (
        <div className="chips" style={{ marginTop: 6 }}>
          {result.cited_sections.map(s => (
            <span key={s} className="section-chip">§{s}</span>
          ))}
        </div>
      )}
      {result.authorized_tool_calls?.length > 0 && (
        <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-muted)' }}>
          Tools: {result.authorized_tool_calls.map(c => c.tool || c.name).join(', ')}
        </div>
      )}
    </div>
  )
}

export default function ComparePanel({ results, loading }) {
  const tiers = ['blue', 'grey', 'red']

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">⚖️ Trust Tier Comparison — same message, three tiers</span>
      </div>
      <div className="card-body">
        <div className="compare-grid">
          {tiers.map(tier => (
            <CompareCard
              key={tier}
              tier={tier}
              result={loading ? null : results?.[tier]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
