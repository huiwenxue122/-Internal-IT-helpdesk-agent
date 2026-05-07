const ICONS = { allow: '✅', deny: '🚫', clarify: '🔶', escalate: '🔀' }

export default function VerdictBadge({ verdict }) {
  const v = (verdict || 'unknown').toLowerCase()
  const icon = ICONS[v] || '❓'
  return (
    <span className={`verdict-badge verdict-${v}`}>
      {icon} {verdict || 'unknown'}
    </span>
  )
}
