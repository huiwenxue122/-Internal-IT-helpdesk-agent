import { findRunAs } from '../runAs'

const TIER_COLOR = { blue: '#3b82f6', grey: '#94a3b8', red: '#ef4444' }
const TIER_LABEL = { blue: '🔵 Blue', grey: '⚪ Grey', red: '🔴 Red' }

function Row({ label, value, mono, highlight }) {
  return (
    <div className="effective-row">
      <span className="effective-key">{label}</span>
      <span
        className={`effective-val${mono ? ' mono' : ''}`}
        style={highlight ? { color: highlight, fontWeight: 700 } : undefined}
      >
        {value}
      </span>
    </div>
  )
}

export default function EffectiveRequest({
  runAsId, effectiveTier, effectiveUserId, effectiveProfile,
  message, selectedScenario, contextDiffers, advancedActive,
}) {
  const runAs = findRunAs(runAsId)
  const runAsLabel = runAs && runAs.id !== 'custom'
    ? `${TIER_LABEL[runAs.tier] || runAs.tier} · ${runAs.label}`
    : '⚙️ Custom'

  return (
    <div className="effective-request">
      <div className="effective-header">
        <span className="effective-title">Effective Request</span>
        <span className="effective-hint">sent on Run</span>
      </div>

      {selectedScenario
        ? <Row label="Scenario" value={selectedScenario.name} />
        : <Row label="Scenario" value="custom message" />}

      <Row
        label="Run As"
        value={runAsLabel}
        highlight={TIER_COLOR[effectiveTier]}
      />
      <Row label="Trust Tier"   value={TIER_LABEL[effectiveTier] || effectiveTier} highlight={TIER_COLOR[effectiveTier]} />
      <Row label="User ID"      value={effectiveUserId || '—'} mono />

      {effectiveProfile && (
        <>
          <Row label="Profile"    value={effectiveProfile.name} />
          <Row label="Dept/Team"  value={effectiveProfile.department || '—'} />
          <Row label="Manager"    value={effectiveProfile.is_manager ? 'Yes' : 'No'} />
          {effectiveProfile.reports?.length > 0 && (
            <Row label="Reports"  value={effectiveProfile.reports.join(', ')} mono />
          )}
          {effectiveProfile.verified === false && (
            <Row label="Verified" value="No" highlight="var(--deny)" />
          )}
        </>
      )}

      <Row
        label="Message"
        value={message
          ? `"${message.slice(0, 70)}${message.length > 70 ? '…' : '"'}`
          : '(empty)'}
      />

      {advancedActive && (
        <div className="effective-diff-warn">
          ⚙️ Advanced override active — manually configured values are in use.
        </div>
      )}

      {!advancedActive && contextDiffers && (
        <div className="effective-diff-warn">
          ⚠️ Custom context — differs from the scenario's suggested values.
        </div>
      )}
    </div>
  )
}
