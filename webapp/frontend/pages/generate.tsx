import { useEffect, useState } from 'react'
import { api } from '../lib/api'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function GeneratePage() {
  const [years, setYears] = useState<{ id: number; name: string }[]>([])
  const [yearId, setYearId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ success: boolean; status: string; message?: string; conflicts: string[] } | null>(null)

  useEffect(() => {
    api.years().then((y) => { setYears(y); if (y[0]) setYearId(y[0].id); }).catch(console.error)
  }, [])

  async function generate() {
    if (!yearId) return
    setLoading(true)
    setResult(null)
    try {
      // 1. Start job
      const startRes = await api.generate(yearId, 0)
      if (!startRes.job_id) {
        throw new Error("No job_id returned")
      }
      const jobId = startRes.job_id

      // 2. Poll status
      while (true) {
        await new Promise(r => setTimeout(r, 2000))
        const res = await fetch(`${API}/api/schedule/generate/status/${jobId}`)

        if (!res.ok) {
          // If job not found (server restarted?) or other error, stop.
          throw new Error("Job lost or server unreachable. Please try again.")
        }

        const statusRes = await res.json()

        if (statusRes.status === "completed" || statusRes.status === "failed") {
          setResult(statusRes.result)
          setLoading(false)
          break
        }
      }

    } catch (e: any) {
      setResult({ success: false, status: 'ERROR', message: e.message, conflicts: [] })
      setLoading(false)
    }
  }

  function exportExcel() {
    if (!yearId) return
    window.open(`${API}/api/export/excel?year_id=${yearId}`, '_blank')
  }

  return (
    <div>
      <h1>Generate Schedule</h1>
      <div className="form-group">
        <label>Year</label>
        <select value={yearId || ''} onChange={(e) => setYearId(Number(e.target.value))}>
          {years.map((y) => (
            <option key={y.id} value={y.id}>{y.name}</option>
          ))}
        </select>
      </div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <button className="btn" onClick={generate} disabled={loading || !yearId}>
          {loading ? 'Solving... (no time limit—leave tab open)' : 'Generate Schedule'}
        </button>
        <button className="btn secondary" onClick={exportExcel} disabled={!yearId}>
          Export to Excel
        </button>
      </div>
      {result && (
        <div className={`alert ${result.success ? 'success' : 'error'}`}>
          <strong>{result.success ? 'Success' : 'Failed'}</strong> — {result.status}
          {result.message && <p>{result.message}</p>}
          {result.conflicts?.length > 0 && (
            <ul style={{ marginTop: 8 }}>
              {result.conflicts.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
        Runs OR-Tools CP-SAT to assign rotations per resident while satisfying coverage, night caps,
        ED rules, Ramirez restriction, and clinic cadence. No time limit—can run for hours.
      </p>
    </div>
  )
}
