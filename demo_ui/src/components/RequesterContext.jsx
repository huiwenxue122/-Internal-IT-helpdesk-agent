import { PROFILES } from '../profiles'

const TIERS = [
  { id: 'blue', label: 'Blue', icon: '🔵' },
  { id: 'grey', label: 'Grey', icon: '⚪' },
  { id: 'red',  label: 'Red',  icon: '🔴' },
]

export default function RequesterContext({ trustTier, setTrustTier, selectedProfileId, onProfileChange, userId, setUserId }) {
  const profile = PROFILES.find(p => p.id === selectedProfileId)

  return (
    <div className="sidebar-section">
      <div className="sidebar-label">Requester Context</div>

      {/* Trust tier */}
      <div className="form-group">
        <label>Trust Tier</label>
        <div className="tier-btns">
          {TIERS.map(t => (
            <button
              key={t.id}
              className={`tier-btn ${trustTier === t.id ? `active-tier-${t.id}` : ''}`}
              onClick={() => setTrustTier(t.id)}
              title={`Set trust tier to ${t.label}`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Requester profile */}
      <div className="form-group">
        <label>Requester Profile</label>
        <select
          value={selectedProfileId}
          onChange={e => onProfileChange(e.target.value)}
        >
          {PROFILES.map(p => (
            <option key={p.id} value={p.id}>{p.label}</option>
          ))}
        </select>
        {profile && (
          <div className="profile-preview">
            <span className="profile-chip">{profile.subtitle}</span>
            {profile.data.is_manager && (
              <span className="profile-chip profile-chip-mgr">Manager</span>
            )}
            {profile.data.verified === false && (
              <span className="profile-chip profile-chip-warn">Unverified</span>
            )}
          </div>
        )}
      </div>

      {/* User ID */}
      <div className="form-group">
        <label>User ID</label>
        <input
          type="text"
          value={userId}
          onChange={e => setUserId(e.target.value)}
          placeholder="EMP-2200"
        />
      </div>
    </div>
  )
}
