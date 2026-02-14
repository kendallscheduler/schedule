import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function RequirementsPage() {
  const [reqs, setReqs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editWeeks, setEditWeeks] = useState('')

  useEffect(() => {
    load()
  }, [])

  function load() {
    setLoading(true)
    api.requirements()
      .then(setReqs)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  async function handleSync() {
    setSyncing(true)
    setMsg(null)
    try {
      const res = await api.syncRequirements()
      setMsg(`Synced to standard spec: ${res.total_requirements} requirements`)
      load()
    } catch (e: any) {
      setMsg(`Error: ${e.message}`)
    } finally {
      setSyncing(false)
    }
  }

  async function saveEdit(req: any) {
    const w = parseInt(editWeeks, 10)
    if (isNaN(w) || w < 0) return
    try {
      await api.updateRequirement(req.id, { required_weeks: w })
      setEditingId(null)
      load()
    } catch (e: any) {
      setMsg(`Error: ${e.message}`)
    }
  }

  const byPgy: Record<string, any[]> = {}
  for (const r of reqs) {
    if (!byPgy[r.pgy]) byPgy[r.pgy] = []
    byPgy[r.pgy].push(r)
  }
  const pgyOrder = ['PGY1', 'PGY2', 'PGY3', 'TY']

  return (
    <div>
      <h1>Requirements (per PGY)</h1>
      <p style={{ color: '#94a3b8', marginBottom: 24 }}>
        Core electives (Cardio 4, ID 2, Neuro 2, ED 4, Geriatrics 2) apply to PGY1–PGY3 only, cumulative. TY: 16 Floors (4 nights, 12 days), 4 ICU (2 day, 2 ICUN). NF counts as floors. SWING counts as NF or ICU night (whichever needed). ICU days and nights interchangeable.
      </p>
      <div style={{ marginBottom: 24 }}>
        <button
          className="btn"
          onClick={handleSync}
          disabled={syncing}
        >
          {syncing ? 'Syncing...' : 'Sync to standard spec'}
        </button>
        <span style={{ marginLeft: 12, fontSize: '0.9rem', color: '#94a3b8' }}>
          Applies PGY1–3, TY requirements including ICU, Geriatrics, subspecialties
        </span>
      </div>
      {msg && (
        <div className={`alert ${msg.startsWith('Error') ? 'error' : 'success'}`}>
          {msg}
        </div>
      )}
      {loading && <p>Loading...</p>}
      {!loading && (
        <table>
          <thead>
            <tr>
              <th>PGY</th>
              <th>Category</th>
              <th>Required Weeks</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {pgyOrder.map((pgy) =>
              (byPgy[pgy] || []).map((r) => {
                const isEditing = editingId === r.id
                return (
                  <tr key={r.id}>
                    <td>{r.pgy}</td>
                    <td>{r.category}</td>
                    <td>
                      {isEditing ? (
                        <input
                          type="number"
                          min={0}
                          value={editWeeks}
                          onChange={(e) => setEditWeeks(e.target.value)}
                          onBlur={() => saveEdit(r)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit(r)
                            if (e.key === 'Escape') setEditingId(null)
                          }}
                          autoFocus
                          style={{ width: 64, padding: 4 }}
                        />
                      ) : (
                        <button
                          type="button"
                          className="btn secondary"
                          style={{ padding: '2px 8px', fontSize: '0.9rem' }}
                          onClick={() => {
                            setEditingId(r.id)
                            setEditWeeks(String(r.required_weeks))
                          }}
                        >
                          {r.required_weeks} ✎
                        </button>
                      )}
                    </td>
                    <td></td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
