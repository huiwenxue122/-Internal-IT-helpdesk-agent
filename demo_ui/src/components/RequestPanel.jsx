const TIERS = ['blue', 'grey', 'red']

export default function RequestPanel({ form, setForm, onRun, loading }) {
  const update = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  return (
    <div className="sidebar-section">
      <div className="sidebar-label">Request</div>

      <div className="form-group">
        <label>Trust Tier</label>
        <div className="tier-btns">
          {TIERS.map(t => (
            <button
              key={t}
              className={`tier-btn ${form.trust_tier === t ? `active-tier-${t}` : ''}`}
              onClick={() => setForm(f => ({ ...f, trust_tier: t }))}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>User ID</label>
        <input
          type="text"
          value={form.user_id}
          onChange={update('user_id')}
          placeholder="EMP-2200"
        />
      </div>

      <div className="form-group">
        <label>Message</label>
        <textarea
          value={form.message}
          onChange={update('message')}
          placeholder="Type your helpdesk request…"
          rows={5}
        />
      </div>

      <button className="run-btn" onClick={onRun} disabled={loading || !form.message.trim()}>
        {loading ? 'Running…' : '▶ Run Agent'}
      </button>
    </div>
  )
}
