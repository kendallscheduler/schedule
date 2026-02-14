import { useEffect, useState } from 'react'
import { api } from '../lib/api'

const API = '' // Same-origin; Next.js proxies /api/* to backend

export default function RolloverPage() {
  const [mode, setMode] = useState<'db' | 'excel'>('db')
  const [years, setYears] = useState<{ id: number; name: string }[]>([])
  const [sourceYearId, setSourceYearId] = useState<number | null>(null)
  const [targetName, setTargetName] = useState('2026-2027')
  const [internCount, setInternCount] = useState(14)
  const [tyCount, setTyCount] = useState(8)
  const [includePgy3, setIncludePgy3] = useState(false)
  const [excelFile, setExcelFile] = useState<File | null>(null)
  const [cohortsConfig, setCohortsConfig] = useState([
    { cohort_id: 1, target_interns: 4 },
    { cohort_id: 2, target_interns: 2 },
    { cohort_id: 3, target_interns: 2 },
    { cohort_id: 4, target_interns: 2 },
    { cohort_id: 5, target_interns: 2 },
  ])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  async function loadYears() {
    const y = await api.years()
    setYears(y)
    if (y[0]) setSourceYearId(y[0].id)
  }
  useEffect(() => { loadYears().catch(console.error) }, [])

  async function deleteYear(yearId: number) {
    if (deleteConfirm !== yearId) return
    setDeleting(true)
    setError(null)
    try {
      const r = await api.deleteYear(yearId)
      setDeleteConfirm(null)
      await loadYears()
      setResult({ deleted: r.deleted })
    } catch (e: any) {
      setError(e.message)
    } finally {
      setDeleting(false)
    }
  }

  async function runRollover() {
    if (mode === 'excel') {
      if (!excelFile || !targetName) return
      setLoading(true)
      setResult(null)
      setError(null)
      try {
        const fd = new FormData()
        fd.append('file', excelFile)
        const params = new URLSearchParams({
          target_year_name: targetName,
          intern_count: String(internCount),
          ty_count: String(tyCount),
          include_pgy3: String(includePgy3),
          cohort_1_target: String(cohortsConfig[0]?.target_interns ?? 4),
          cohort_2_target: String(cohortsConfig[1]?.target_interns ?? 2),
          cohort_3_target: String(cohortsConfig[2]?.target_interns ?? 2),
          cohort_4_target: String(cohortsConfig[3]?.target_interns ?? 2),
          cohort_5_target: String(cohortsConfig[4]?.target_interns ?? 2),
        })
        const r = await fetch(`${API}/api/rollover/from-excel?${params}`, { method: 'POST', body: fd })
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || JSON.stringify(data))
        setResult(data)
        await loadYears()
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
      return
    }
    if (!sourceYearId || !targetName) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const r = await fetch(`${API}/api/rollover/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_year_id: sourceYearId,
          target_year_name: targetName,
          intern_count: internCount,
          ty_count: tyCount,
          include_pgy3: includePgy3,
          cohorts_config: cohortsConfig,
        }),
      })
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || JSON.stringify(data))
      setResult(data)
      await loadYears()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Next Year Rollover</h1>
      <p style={{ color: '#94a3b8', marginBottom: 24 }}>
        Create next year roster: PGY1→PGY2, PGY2→PGY3, PGY3→graduate (unless included). TY does not roll over — they graduate,
        so TY slots are open for new incoming TYs, just like intern slots are open for new PGY1s.
      </p>
      <div className="form-group">
        <label>Source</label>
        <select value={mode} onChange={(e) => setMode(e.target.value as 'db' | 'excel')}>
          <option value="db">From current year in database</option>
          <option value="excel">Import from Excel (current schedule)</option>
        </select>
      </div>
      {mode === 'excel' && (
        <div className="form-group">
          <label>Current Schedule Excel</label>
          <p style={{ fontSize: '0.9rem', color: '#94a3b8' }}>SCHEDULE sheet, rows 4-56, cols A=Cohort, B=PGY, C=Name</p>
          <input type="file" accept=".xlsx,.xls" onChange={(e) => setExcelFile(e.target.files?.[0] || null)} />
        </div>
      )}
      {mode === 'db' && (
      <div className="form-group">
        <label>Source Year (current)</label>
        <select value={sourceYearId || ''} onChange={(e) => setSourceYearId(Number(e.target.value))}>
          {years.map((y) => (
            <option key={y.id} value={y.id}>{y.name}</option>
          ))}
        </select>
      </div>
      )}
      <div className="form-group">
        <label>Target Year Name</label>
        <input value={targetName} onChange={(e) => setTargetName(e.target.value)} placeholder="2026-2027" />
      </div>
      <div className="form-group">
        <label>Incoming PGY1 Interns (placeholders)</label>
        <input type="number" min={0} max={30} value={internCount} onChange={(e) => setInternCount(Number(e.target.value))} />
      </div>
      <div className="form-group">
        <label>Incoming TYs (placeholders)</label>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: 4, marginBottom: 4 }}>
          TYs graduate and do not roll over. These slots are for new TYs, same as interns for PGY1.
        </p>
        <input type="number" min={0} max={20} value={tyCount} onChange={(e) => setTyCount(Number(e.target.value))} />
      </div>
      <div className="form-group">
        <label>
          <input type="checkbox" checked={includePgy3} onChange={(e) => setIncludePgy3(e.target.checked)} />
          {' '}Include graduating PGY3 (chief coverage)
        </label>
      </div>
      <h3>Cohort Target Interns</h3>
      {cohortsConfig.map((c, i) => (
        <div key={c.cohort_id} className="form-group" style={{ display: 'inline-block', marginRight: 16 }}>
          <label>Cohort {c.cohort_id}</label>
          <input type="number" min={0} max={8} value={c.target_interns} style={{ width: 60 }}
            onChange={(e) => {
              const next = [...cohortsConfig]
              next[i] = { ...next[i], target_interns: Number(e.target.value) }
              setCohortsConfig(next)
            }} />
        </div>
      ))}
      <div style={{ marginTop: 24 }}>
        <button className="btn" onClick={runRollover} disabled={loading || (mode === 'db' && !sourceYearId) || (mode === 'excel' && !excelFile)}>
          {loading ? 'Running...' : 'Rollover to Next Year'}
        </button>
      </div>
      {error && <div className="alert error">{error}</div>}
      {result && (
        <div className="alert success">
          {result.deleted ? (
            <><strong>Deleted year:</strong> {result.deleted}</>
          ) : (
            <>
              <strong>Rollover complete</strong>
              <p>Target year: {result.target_year_name} (ID: {result.target_year_id})</p>
              <p>Promoted: {result.promoted_count} | Intern placeholders: {result.intern_placeholders} | TY placeholders: {result.ty_placeholders}</p>
              <p>Total residents: {result.total_residents}</p>
            </>
          )}
        </div>
      )}
      <h3 style={{ marginTop: 32 }}>Delete Year</h3>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: 12 }}>
        Permanently remove a year and all its residents, schedule, cohorts, and vacation requests. This cannot be undone.
      </p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
        {years.map((y) => (
          <span key={y.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{y.name}</span>
            {deleteConfirm === y.id ? (
              <>
                <button className="btn" style={{ background: '#dc2626', color: 'white', padding: '4px 10px', fontSize: '0.85rem' }}
                  onClick={() => deleteYear(y.id)} disabled={deleting}>Confirm delete</button>
                <button className="btn secondary" style={{ padding: '4px 10px', fontSize: '0.85rem' }}
                  onClick={() => setDeleteConfirm(null)}>Cancel</button>
              </>
            ) : (
              <button className="btn secondary" style={{ padding: '4px 10px', fontSize: '0.85rem' }}
                onClick={() => setDeleteConfirm(y.id)}>Delete</button>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}
