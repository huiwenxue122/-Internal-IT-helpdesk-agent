import VerdictBadge from './VerdictBadge'

export default function ResponseCard({ result }) {
  const riskClass = { high: 'risk-high', medium: 'risk-medium', low: 'risk-low' }[result.risk_level] || 'risk-unknown'

  return (
    <div className="card">
      <div className="card-header">
        <div className="response-meta">
          <VerdictBadge verdict={result.verdict} />
          <span className={`risk-badge ${riskClass}`}>Risk: {result.risk_level || 'unknown'}</span>
          {result.intent && (
            <span className="chip chip-purple">{result.intent.replace(/_/g, ' ')}</span>
          )}
        </div>
      </div>
      <div className="card-body">
        <p className="response-text">{result.response || '(no response)'}</p>

        {result.cited_sections?.length > 0 && (
          <div className="cited-sections">
            {result.cited_sections.map(s => (
              <span key={s} className="section-chip">§{s}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
