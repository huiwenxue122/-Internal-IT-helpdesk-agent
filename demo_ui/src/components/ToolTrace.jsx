function ToolList({ label, tools, variant }) {
  const chipClass = { green: 'chip-green', red: 'chip-red', default: '' }[variant] || ''
  return (
    <div>
      <div className="trace-section-title">{label}</div>
      {tools?.length > 0 ? (
        <div className="chips">
          {tools.map((t, i) => {
            const name = typeof t === 'string' ? t : (t.tool || t.name || JSON.stringify(t))
            return <span key={i} className={`chip ${chipClass}`}>{name}</span>
          })}
        </div>
      ) : (
        <div className="empty-state">None.</div>
      )}
    </div>
  )
}

function ToolCallList({ label, calls, variant }) {
  const chipClass = { green: 'chip-green', red: 'chip-red' }[variant] || ''
  if (!calls?.length) {
    return (
      <div>
        <div className="trace-section-title">{label}</div>
        <div className="empty-state">None.</div>
      </div>
    )
  }
  return (
    <div>
      <div className="trace-section-title">{label}</div>
      {calls.map((c, i) => (
        <div key={i} className="tool-entry">
          <span className={`chip ${chipClass}`}>{c.tool || c.name || '?'}</span>
          {c.reason && <span className="tool-reason">{c.reason}</span>}
        </div>
      ))}
    </div>
  )
}

export default function ToolTrace({ result }) {
  const blockedTools = (result.blocked_by_guard || []).map(b =>
    typeof b === 'string' ? b : (b.tool || b.reason || JSON.stringify(b))
  )

  return (
    <div>
      <ToolCallList
        label={`Proposed Tool Calls (${result.allowed_tool_calls?.length ?? 0})`}
        calls={result.allowed_tool_calls}
        variant="default"
      />
      <ToolCallList
        label={`Authorized by Guard (${result.authorized_tool_calls?.length ?? 0})`}
        calls={result.authorized_tool_calls}
        variant="green"
      />

      <div className="trace-section-title">
        Executed Tools ({result.executed_tools?.length ?? 0})
      </div>
      {result.executed_tools?.length > 0 ? (
        <div className="chips">
          {result.executed_tools.map((t, i) => (
            <span key={i} className="chip chip-green">{t}</span>
          ))}
        </div>
      ) : <div className="empty-state">No tools executed.</div>}

      <div className="trace-section-title">
        Blocked by Guard ({blockedTools.length})
      </div>
      {blockedTools.length > 0 ? (
        <div className="chips">
          {blockedTools.map((t, i) => <span key={i} className="chip chip-red">{t}</span>)}
        </div>
      ) : <div className="empty-state">Nothing blocked.</div>}
    </div>
  )
}
