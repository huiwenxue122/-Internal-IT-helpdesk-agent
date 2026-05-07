import { useState } from 'react'
import { PROFILES } from '../profiles'

const TIERS = [
  { id: 'blue', label: '🔵 Blue' },
  { id: 'grey', label: '⚪ Grey' },
  { id: 'red',  label: '🔴 Red' },
]

export default function AdvancedOverrides({
  effectiveTier, effectiveUserId, effectiveProfileId,
  advTier, setAdvTier,
  advUserId, setAdvUserId,
  advProfileId, setAdvProfileId,
  advancedActive,
  onReset,
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="sidebar-section advanced-section">
      <button
        className={`advanced-toggle ${open ? 'advanced-toggle-open' : ''}`}
        onClick={() => setOpen(o => !o)}
      >
        <span className="adv-arrow">{open ? '▾' : '▸'}</span>
        <span>Advanced Overrides</span>
        {advancedActive && <span className="adv-active-dot" title="Override active" />}
      </button>

      {open && (
        <div className="advanced-body">
          {advancedActive && (
            <div className="adv-active-banner">
              ⚙️ Override active — Run As defaults are bypassed.
            </div>
          )}

          <div className="form-group">
            <label>Trust Tier Override</label>
            <div className="tier-btns">
              {TIERS.map(t => (
                <button
                  key={t.id}
                  className={`tier-btn ${effectiveTier === t.id ? `active-tier-${t.id}` : ''}`}
                  onClick={() => setAdvTier(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>
            {advTier && <div className="override-note">overriding Run As tier</div>}
          </div>

          <div className="form-group">
            <label>User ID Override</label>
            <input
              type="text"
              value={advUserId !== null ? advUserId : effectiveUserId}
              onChange={e => setAdvUserId(e.target.value)}
              placeholder={effectiveUserId}
            />
            {advUserId !== null && <div className="override-note">overriding Run As user ID</div>}
          </div>

          <div className="form-group">
            <label>Profile Override</label>
            <select
              value={advProfileId || effectiveProfileId}
              onChange={e => setAdvProfileId(e.target.value)}
            >
              {PROFILES.map(p => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
            {advProfileId && <div className="override-note">overriding Run As profile</div>}
          </div>

          {advancedActive && (
            <button className="reset-adv-btn" onClick={onReset}>
              ↺ Reset to Run As defaults
            </button>
          )}
        </div>
      )}
    </div>
  )
}
