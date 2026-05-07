import { useState } from 'react'
import { findProfile } from '../profiles'

const CATEGORIES = [
  { id: 'clearly_allowed', label: '✅ Clearly Allowed', defaultOpen: true },
  { id: 'clearly_denied',  label: '🚫 Clearly Denied',  defaultOpen: false },
  { id: 'ambiguous',       label: '🔶 Ambiguous',        defaultOpen: false },
  { id: 'adversarial',     label: '🔴 Adversarial',      defaultOpen: false },
]

const TIER_LABEL = { blue: '🔵 Blue', grey: '⚪ Grey', red: '🔴 Red' }

export default function ScenarioPicker({ scenarios, selectedId, onSelect, onApplySuggested }) {
  const [open, setOpen] = useState(() =>
    Object.fromEntries(CATEGORIES.map(c => [c.id, c.defaultOpen]))
  )

  const toggle = (catId) => setOpen(prev => ({ ...prev, [catId]: !prev[catId] }))

  // Group scenarios by category
  const byCategory = {}
  for (const s of scenarios) {
    if (!byCategory[s.category]) byCategory[s.category] = []
    byCategory[s.category].push(s)
  }

  const selected = scenarios.find(s => s.id === selectedId)
  const sugProfile = selected?.suggested_profile_id ? findProfile(selected.suggested_profile_id) : null

  return (
    <div className="sidebar-section scenario-picker">
      <div className="sidebar-label">Official Test Scenarios (21)</div>
      <p className="sidebar-help">
        Templates update only the message. Trust tier and profile are
        controlled separately — use <em>Apply suggested context</em> to
        pre-fill with the take-home spec values.
      </p>

      {CATEGORIES.map(cat => {
        const items = byCategory[cat.id] || []
        if (!items.length) return null
        const isOpen = open[cat.id]

        return (
          <div key={cat.id} className="cat-group">
            <button
              className={`cat-header ${isOpen ? 'cat-open' : ''}`}
              onClick={() => toggle(cat.id)}
              title={`${isOpen ? 'Collapse' : 'Expand'} ${cat.label}`}
            >
              <span className="cat-arrow">{isOpen ? '▾' : '▸'}</span>
              <span className="cat-label">{cat.label}</span>
              <span className="cat-count">{items.length}</span>
            </button>

            {isOpen && items.map(s => (
              <button
                key={s.id}
                className={`scenario-btn ${selectedId === s.id ? 'active' : ''}`}
                onClick={() => onSelect(s)}
                title={s.description}
              >
                {s.name}
              </button>
            ))}
          </div>
        )
      })}

      {/* Suggested context hint for currently selected scenario */}
      {selected && (
        <div className="rec-hint">
          <div className="rec-hint-title">Suggested context</div>
          <div className="rec-hint-rows">
            {selected.suggested_trust_tier && (
              <div className="rec-row">
                <span className="rec-key">Tier</span>
                <span className="rec-val">{TIER_LABEL[selected.suggested_trust_tier] || selected.suggested_trust_tier}</span>
              </div>
            )}
            {selected.suggested_user_id && (
              <div className="rec-row">
                <span className="rec-key">User ID</span>
                <span className="rec-val mono">{selected.suggested_user_id}</span>
              </div>
            )}
            {sugProfile && (
              <div className="rec-row">
                <span className="rec-key">Profile</span>
                <span className="rec-val">{sugProfile.label}</span>
              </div>
            )}
          </div>
          <button
            className="rec-apply-btn"
            onClick={() => onApplySuggested(selected)}
          >
            ↩ Use suggested context
          </button>
          <p className="rec-note">
            {selected.description}
          </p>
        </div>
      )}
    </div>
  )
}
