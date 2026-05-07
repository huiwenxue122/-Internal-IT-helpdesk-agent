import { useState } from 'react'
import { RUN_AS_OPTIONS, TIER_GROUPS } from '../runAs'

const TIER_COLOR = { blue: '#3b82f6', grey: '#94a3b8', red: '#ef4444' }

export default function RunAsSelector({ runAsId, onChange }) {
  // Blue open by default; Grey and Red collapsed
  const [open, setOpen] = useState({ blue: true, grey: false, red: false, null: true })

  const toggle = (tier) => setOpen(prev => ({ ...prev, [tier]: !prev[tier] }))

  return (
    <div className="sidebar-section">
      <div className="sidebar-label">Run As</div>
      <p className="sidebar-help">Who is making this request?</p>

      {TIER_GROUPS.map(group => {
        const key = group.tier ?? 'null'
        const isOpen = open[key]
        const isCustomGroup = group.tier === null
        const groupColor = group.tier ? TIER_COLOR[group.tier] : 'var(--text-light)'
        const items = group.optionIds.map(id => RUN_AS_OPTIONS.find(o => o.id === id)).filter(Boolean)
        const activeInGroup = items.some(o => o.id === runAsId)

        return (
          <div key={key} className="runas-group">
            {/* Collapsible group header — not shown for Custom (just one item) */}
            {!isCustomGroup ? (
              <button
                className={`runas-group-toggle ${isOpen ? 'runas-group-open' : ''}`}
                onClick={() => toggle(key)}
              >
                <span className="cat-arrow">{isOpen ? '▾' : '▸'}</span>
                <span style={{ color: groupColor, fontWeight: 600, fontSize: 11 }}>
                  {group.label}
                </span>
                <span className="cat-count">{items.length}</span>
                {activeInGroup && !isOpen && (
                  <span className="runas-group-active-dot" title="Current selection is in this group" />
                )}
              </button>
            ) : null}

            {/* Items — always visible for Custom group; toggle for tier groups */}
            {(isCustomGroup || isOpen) && items.map(opt => {
              const active = runAsId === opt.id
              return (
                <button
                  key={opt.id}
                  className={`runas-item ${active ? `runas-active runas-active-${opt.tier || 'custom'}` : ''}`}
                  onClick={() => onChange(opt.id)}
                  title={opt.sublabel}
                >
                  <span className="runas-item-label">{opt.label}</span>
                  <span className="runas-item-sub">{opt.sublabel}</span>
                  {active && <span className="runas-check">✓</span>}
                </button>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
