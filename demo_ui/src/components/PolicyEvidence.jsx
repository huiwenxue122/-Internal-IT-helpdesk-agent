function SectionRow({ s }) {
  return (
    <tr>
      <td><code>{s.section_id}</code></td>
      <td>{s.title}</td>
      <td>{s.domain}</td>
      <td>{s.modality}</td>
      <td style={{ fontFamily: 'var(--mono)', fontSize: '11px' }}>
        {s.distance != null ? s.distance.toFixed(4) : '—'}
      </td>
    </tr>
  )
}

function RuleRow({ r }) {
  return (
    <tr>
      <td><code>{r.rule_id}</code></td>
      <td><code>{r.section_id}</code></td>
      <td>{r.modality}</td>
      <td>{r.action}</td>
      <td>{r.risk_level}</td>
      <td style={{ color: 'var(--text-muted)', maxWidth: 200 }}>{r.text_excerpt}</td>
    </tr>
  )
}

export default function PolicyEvidence({ result }) {
  const hasSections = result.retrieved_sections?.length > 0
  const hasRules = result.retrieved_rules?.length > 0
  const hasExpanded = result.graph_expanded_rules?.length > 0

  return (
    <div>
      <div className="trace-section-title">Retrieved Sections ({result.retrieved_sections?.length ?? 0})</div>
      {hasSections ? (
        <table className="trace-table">
          <thead>
            <tr>
              <th>ID</th><th>Title</th><th>Domain</th><th>Modality</th><th>Distance</th>
            </tr>
          </thead>
          <tbody>
            {result.retrieved_sections.map(s => <SectionRow key={s.section_id} s={s} />)}
          </tbody>
        </table>
      ) : <div className="empty-state">No sections retrieved.</div>}

      <div className="trace-section-title">
        Retrieved Rules ({result.retrieved_rules?.length ?? 0})
      </div>
      {hasRules ? (
        <table className="trace-table">
          <thead>
            <tr>
              <th>Rule ID</th><th>Section</th><th>Modality</th><th>Action</th><th>Risk</th><th>Excerpt</th>
            </tr>
          </thead>
          <tbody>
            {result.retrieved_rules.map(r => <RuleRow key={r.rule_id} r={r} />)}
          </tbody>
        </table>
      ) : <div className="empty-state">No rules retrieved.</div>}

      {hasExpanded && (
        <>
          <div className="trace-section-title">
            Graph Expanded Rules ({result.graph_expanded_rules.length})
          </div>
          <table className="trace-table">
            <thead>
              <tr>
                <th>Rule ID</th><th>Section</th><th>Modality</th><th>Action</th><th>Risk</th><th>Excerpt</th>
              </tr>
            </thead>
            <tbody>
              {result.graph_expanded_rules.map(r => <RuleRow key={r.rule_id} r={r} />)}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
