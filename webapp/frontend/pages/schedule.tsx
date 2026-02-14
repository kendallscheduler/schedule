import React, { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { api } from '../lib/api'

// Display label for rotation
const ROT_LABEL: Record<string, string> = {
  A: 'A', B: 'B', C: 'C', D: 'D', G: 'G',
  ICU: 'ICU', 'ICU N': 'ICU N',
  NF: 'NF', SWING: 'SWING',
  CLINIC: 'CLINIC', 'CLINIC *': 'CLINIC*',
  ED: 'ED', VACATION: 'VAC',
  CARDIO: 'CARDIO',
  ID: 'ID', NEURO: 'NEURO', GERIATRICS: 'GERI',
  ELECTIVE: 'ELECT', 'GEN SURG': 'SURG',
  'TY CLINIC': 'TY CL',
}
const ROT_OPTIONS = [
  '', 'A', 'B', 'C', 'D', 'G',
  'ICU', 'ICU N',
  'NF', 'SWING', 'CLINIC', 'CLINIC *',
  'ED', 'VACATION', 'CARDIO',
  'ID', 'NEURO', 'GERIATRICS',
  'ELECTIVE', 'GEN SURG', 'TY CLINIC',
]
function rotLabel(code: string): string {
  return ROT_LABEL[code] ?? code
}

// Background colors by rotation category
const ROT_COLORS: Record<string, string> = {
  A: '#86efac', B: '#86efac', C: '#86efac', D: '#86efac', G: '#86efac',
  ICU: '#7dd3fc', 'ICU N': '#38bdf8',
  CLINIC: '#93c5fd', 'CLINIC *': '#93c5fd', ED: '#93c5fd',
  VACATION: '#fca5a5', NF: '#e2e8f0', SWING: '#c4b5fd',
  CARDIO: '#fdba74',
  ID: '#fef08a', NEURO: '#fef08a', GERIATRICS: '#fef08a',
  ELECTIVE: '#fef08a', 'GEN SURG': '#93c5fd',
  'TY CLINIC': '#93c5fd',
}

// Week date ranges for this year's schedule (52 weeks)
const WEEK_DATES = [
  '07/01-07/06', '07/07-07/13', '07/14-07/20', '07/21-07/27', '07/28-08/03',
  '08/04-08/10', '08/11-08/17', '08/18-08/24', '08/25-08/31', '09/01-09/07',
  '09/08-09/14', '09/15-09/21', '09/22-09/28', '09/29-10/05', '10/06-10/12',
  '10/13-10/19', '10/20-10/26', '10/27-11/02', '11/03-11/09', '11/10-11/16',
  '11/17-11/23', '11/24-11/30', '12/01-12/07', '12/08-12/14', '12/15-12/21',
  '12/22-12/28', '12/29-01/04', '01/05-01/11', '01/12-01/18', '01/19-01/25',
  '01/26-02/01', '02/02-02/08', '02/09-02/15', '02/16-02/22', '02/23-03/01',
  '03/02-03/08', '03/09-03/15', '03/16-03/22', '03/23-03/29', '03/30-04/05',
  '04/06-04/12', '04/13-04/19', '04/20-04/26', '04/27-05/03', '05/04-05/10',
  '05/11-05/17', '05/18-05/24', '05/25-05/31', '06/01-06/07', '06/08-06/14',
  '06/15-06/21', '06/22-06/30',
]
function getWeekSpan(weekNum: number, _startDateStr: string): string {
  return WEEK_DATES[weekNum - 1] ?? String(weekNum)
}

const PGY_ORDER: Record<string, number> = { PGY1: 0, PGY2: 1, PGY3: 2, TY: 3 }

export default function SchedulePage() {
  const [years, setYears] = useState<{ id: number; name: string; start_date?: string }[]>([])
  const [residents, setResidents] = useState<any[]>([])
  const [assignments, setAssignments] = useState<Record<number, Record<number, string>>>({})
  const [remaining, setRemaining] = useState<any[]>([])
  const [yearId, setYearId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [filterPgy, setFilterPgy] = useState<string>('')
  const [filterRot, setFilterRot] = useState<string>('')
  const [searchResident, setSearchResident] = useState<string>('')
  const [editingCell, setEditingCell] = useState<{ residentId: number; week: number } | null>(null)
  const [savingCell, setSavingCell] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [clearModal, setClearModal] = useState<{ type: 'resident' | 'all'; resident?: { id: number; name: string } } | null>(null)
  const [clearConfirmText, setClearConfirmText] = useState('')
  const [clearing, setClearing] = useState(false)
  const [backups, setBackups] = useState<{ id: number; description: string; created_at: string }[]>([])
  const [showBackups, setShowBackups] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const scrollTopRef = useRef<HTMLDivElement>(null)
  const scrollBottomRef = useRef<HTMLDivElement>(null)
  const scrollMainRef = useRef<HTMLDivElement>(null)
  const isSyncingRef = useRef(false)
  const syncScroll = useCallback((source: 'top' | 'bottom' | 'main') => {
    if (isSyncingRef.current) return
    const top = scrollTopRef.current
    const bottom = scrollBottomRef.current
    const main = scrollMainRef.current
    if (!main) return
    isSyncingRef.current = true
    const scrollLeft = source === 'top' ? top?.scrollLeft : source === 'bottom' ? bottom?.scrollLeft : main.scrollLeft
    if (source !== 'top' && top) top.scrollLeft = scrollLeft ?? 0
    if (source !== 'bottom' && bottom) bottom.scrollLeft = scrollLeft ?? 0
    if (source !== 'main') main.scrollLeft = scrollLeft ?? 0
    requestAnimationFrame(() => { isSyncingRef.current = false })
  }, [])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!scrollMainRef.current) return
      const step = 200
      if (e.key === 'ArrowRight') {
        scrollMainRef.current.scrollLeft += step
      } else if (e.key === 'ArrowLeft') {
        scrollMainRef.current.scrollLeft -= step
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const blocks = [
    { label: 'Block 1', colspan: 5 },
    { label: 'Block 2', colspan: 5 },
    { label: 'Block 3', colspan: 4 },
    { label: 'Block 5', colspan: 5 },
    { label: 'End of year', colspan: 5 },
    { label: 'Block 6', colspan: 5 },
    { label: 'Block 7', colspan: 5 },
    { label: 'Block 8', colspan: 5 },
    { label: 'Block 9', colspan: 5 },
    { label: 'Block 10', colspan: 8 },
  ]
  const blockEdges = useMemo(() => {
    let sum = 0
    const edges = new Set<number>()
    blocks.forEach(b => {
      sum += b.colspan
      edges.add(sum)
    })
    return edges
  }, [])

  const [yearDetail, setYearDetail] = useState<{ start_date?: string } | null>(null)
  useEffect(() => {
    if (yearId) api.getYear(yearId).then((y: any) => setYearDetail(y)).catch(() => setYearDetail(null))
    else setYearDetail(null)
  }, [yearId])
  const selectedYear = useMemo(() => years.find((y) => y.id === yearId), [years, yearId])
  const startDate = yearDetail?.start_date ?? selectedYear?.start_date ?? (selectedYear ? `${String(selectedYear.name).split('-')[0]}-07-01` : '')

  useEffect(() => {
    api.years().then((y: any) => {
      setYears(y ?? [])
      if (y?.[0]) setYearId(y[0].id)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const refetchSchedule = useCallback(() => {
    if (yearId) {
      api.residents(yearId).then(setResidents)
      api.scheduleAssignments(yearId).then(setAssignments)
      api.remaining(yearId).then(setRemaining)
    }
  }, [yearId])

  useEffect(() => {
    refetchSchedule()
  }, [refetchSchedule])

  useEffect(() => {
    const onVisible = () => refetchSchedule()
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [refetchSchedule])

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === 'schedule-invalidated') refetchSchedule()
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [refetchSchedule])

  useEffect(() => {
    if (yearId && showBackups) api.scheduleBackups(yearId).then(setBackups).catch(() => setBackups([]))
  }, [yearId, showBackups])

  let filtered = residents
  if (filterPgy) filtered = filtered.filter((r) => r.pgy === filterPgy)
  if (filterRot) {
    filtered = filtered.filter((r) => {
      const wks = assignments[r.id] || {}
      return Object.values(wks).includes(filterRot)
    })
  }
  if (searchResident.trim()) {
    const q = searchResident.trim().toLowerCase()
    filtered = filtered.filter((r) =>
      (r.name || '').toLowerCase().includes(q) ||
      (r.cohort_name || '').toLowerCase().includes(q) ||
      (r.pgy || '').toLowerCase().includes(q) ||
      (r.track || '').toLowerCase().includes(q)
    )
  }

  const sortedResidents = useMemo(() => {
    const arr = [...filtered]
    const TRACK_ORDER: Record<string, number> = { anesthesia: 0, neurology: 1 }
    arr.sort((a, b) => {
      const isTyA = a.pgy === 'TY'
      const isTyB = b.pgy === 'TY'
      if (!isTyA && !isTyB) {
        const cohortA = String(a.cohort_name ?? a.cohort_id ?? '')
        const cohortB = String(b.cohort_name ?? b.cohort_id ?? '')
        const c = cohortA.localeCompare(cohortB, undefined, { numeric: true })
        if (c !== 0) return c
        const pa = PGY_ORDER[a.pgy] ?? 99
        const pb = PGY_ORDER[b.pgy] ?? 99
        if (pa !== pb) return pa - pb
        return (a.name || '').localeCompare(b.name || '')
      }
      if (isTyA && !isTyB) return 1
      if (!isTyA && isTyB) return -1
      const trackA = TRACK_ORDER[a.track] ?? 2
      const trackB = TRACK_ORDER[b.track] ?? 2
      if (trackA !== trackB) return trackA - trackB
      return (a.name || '').localeCompare(b.name || '')
    })
    return arr
  }, [filtered])

  // Compute row divider classes: first of cohort/track, first of PGY within cohort
  const rowMeta = useMemo(() => {
    const meta: { isFirstInCohort: boolean; isFirstInPgy: boolean }[] = []
    let prevKey = ''
    let prevPgy = ''
    for (const r of sortedResidents) {
      const key = r.pgy === 'TY' ? `TY:${r.track || 'general'}` : String(r.cohort_name ?? r.cohort_id ?? '')
      const pgy = r.pgy
      meta.push({
        isFirstInCohort: key !== prevKey,
        isFirstInPgy: key !== prevKey || pgy !== prevPgy,
      })
      prevKey = key
      prevPgy = pgy
    }
    return meta
  }, [sortedResidents])

  async function updateCell(residentId: number, week: number, rotationCode: string) {
    if (!yearId) return
    setSavingCell(true)
    setMsg(null)
    try {
      await api.updateAssignment({
        resident_id: residentId,
        year_id: yearId,
        week_number: week,
        rotation_code: rotationCode,
      })
      const [assigns, rem] = await Promise.all([
        api.scheduleAssignments(yearId),
        api.remaining(yearId),
      ])
      setAssignments(assigns)
      setRemaining(rem)
      setEditingCell(null)
      setMsg('Saved. Resident requirements updated.')
    } catch (e: any) {
      setMsg(`Error: ${e?.message || 'Could not save'}`)
    } finally {
      setSavingCell(false)
    }
  }

  async function handleClear() {
    if (!yearId || clearConfirmText !== 'DELETE') return
    setClearing(true)
    setMsg(null)
    try {
      const res = await api.clearSchedule(
        yearId,
        clearModal?.type === 'resident' ? clearModal.resident?.id : undefined,
        clearConfirmText
      )
      setClearModal(null)
      setClearConfirmText('')
      setMsg(`Cleared ${res.cleared} rotation(s). Backup saved.`)
      const [assigns, rem] = await Promise.all([api.scheduleAssignments(yearId), api.remaining(yearId)])
      setAssignments(assigns)
      setRemaining(rem)
      if (showBackups) api.scheduleBackups(yearId).then(setBackups)
    } catch (e: any) {
      setMsg(`Error: ${e?.message || 'Could not clear'}`)
    } finally {
      setClearing(false)
    }
  }

  async function handleRestore(backupId: number) {
    if (!yearId) return
    setRestoring(true)
    setMsg(null)
    try {
      const res = await api.restoreBackup(backupId)
      setMsg(`Restored ${res.restored} rotation(s).`)
      const [assigns, rem] = await Promise.all([api.scheduleAssignments(yearId), api.remaining(yearId)])
      setAssignments(assigns)
      setRemaining(rem)
    } catch (e: any) {
      setMsg(`Error: ${e?.message || 'Could not restore'}`)
    } finally {
      setRestoring(false)
    }
  }

  function countRotationsForResident(residentId: number) {
    const wks = assignments[residentId] || {}
    return Object.keys(wks).filter((w) => wks[Number(w)]).length
  }

  const totalRotations = useMemo(() => {
    let n = 0
    for (const rid of Object.keys(assignments)) n += Object.keys(assignments[Number(rid)] || {}).length
    return n
  }, [assignments])

  return (
    <div>
      <h1>Schedule Grid</h1>
      <p style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '1rem', marginTop: '-0.25rem' }}>
        Click a rotation cell to edit. {searchResident.trim() && sortedResidents.length > 0 && (
          <span style={{ color: '#22c55e', fontWeight: 600 }}>
            • Matching {sortedResidents.length} residents
          </span>
        )}
      </p>

      <div className="card" style={{ padding: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Year</span>
            <select
              value={yearId ?? ''}
              onChange={(e) => setYearId(e.target.value ? Number(e.target.value) : null)}
              style={{ padding: '2px 4px', fontSize: '0.8125rem', width: 100 }}
            >
              <option value="">Select...</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>{y.name}</option>
              ))}
            </select>
          </div>

          <input
            type="text"
            value={searchResident}
            onChange={(e) => setSearchResident(e.target.value)}
            placeholder="Search residents..."
            style={{ width: 140, padding: '4px 8px', fontSize: '0.8125rem' }}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>PGY</span>
            <select value={filterPgy} onChange={(e) => setFilterPgy(e.target.value)} style={{ padding: '2px 4px', fontSize: '0.8125rem' }}>
              <option value="">All</option>
              <option value="PGY1">PGY1</option><option value="PGY2">PGY2</option><option value="PGY3">PGY3</option><option value="TY">TY</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Rot</span>
            <select value={filterRot} onChange={(e) => setFilterRot(e.target.value)} style={{ padding: '2px 4px', fontSize: '0.8125rem', width: 80 }}>
              <option value="">All</option>
              {ROT_OPTIONS.filter(o => o).map(o => <option key={o} value={o}>{rotLabel(o)}</option>)}
            </select>
          </div>

          <div style={{ flex: 1 }} />

          <button className="btn" onClick={() => { if (yearId) window.open(`/api/export/excel?year_id=${yearId}`, '_blank') }} disabled={!yearId} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
            Export
          </button>
          <button className="btn secondary" onClick={() => refetchSchedule()} disabled={!yearId} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
            ⟳ Refresh
          </button>
          <button className="btn danger" onClick={() => setClearModal({ type: 'all' })} disabled={!yearId || totalRotations === 0} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
            Clear
          </button>
        </div>
      </div>
      {
        showBackups && (
          <div style={{ marginBottom: 16, padding: 16, background: '#1e293b', borderRadius: 8, maxWidth: 560 }}>
            <h4 style={{ marginTop: 0, marginBottom: 12 }}>Schedule backups</h4>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: 12 }}>
              Backups are created automatically before clearing. Restore to undo a clear.
            </p>
            {backups.length === 0 ? (
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No backups yet.</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {backups.map((b) => (
                  <li key={b.id} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                    <span style={{ flex: 1, fontSize: '0.9rem' }}>{b.description}</span>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>{b.created_at ? new Date(b.created_at).toLocaleString() : ''}</span>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                      onClick={() => handleRestore(b.id)}
                      disabled={restoring}
                    >
                      {restoring ? 'Restoring...' : 'Restore'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      }
      {msg && <div className={`alert ${msg.startsWith('Error') ? 'error' : 'success'}`} style={{ marginBottom: 16 }}>{msg}</div>}
      {
        clearModal && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => !clearing && setClearModal(null)}>
            <div style={{ background: '#1e293b', padding: 24, borderRadius: 12, maxWidth: 420, width: '90%' }} onClick={(e) => e.stopPropagation()}>
              <h3 style={{ marginTop: 0, marginBottom: 12, color: '#fca5a5' }}>
                {clearModal.type === 'all' ? 'Clear entire schedule?' : `Clear rotations for ${clearModal.resident?.name}?`}
              </h3>
              <p style={{ color: '#94a3b8', marginBottom: 16, fontSize: '0.95rem' }}>
                {clearModal.type === 'all'
                  ? `This will delete ${totalRotations} rotation(s) for all residents. A backup will be created.`
                  : `This will delete ${countRotationsForResident(clearModal.resident?.id ?? 0)} rotation(s) for this resident. A backup will be created.`}
              </p>
              <p style={{ color: '#e2e8f0', marginBottom: 8, fontSize: '0.9rem' }}>
                Type <strong>DELETE</strong> below to confirm:
              </p>
              <input
                type="text"
                value={clearConfirmText}
                onChange={(e) => setClearConfirmText(e.target.value)}
                placeholder="DELETE"
                autoFocus
                style={{ width: '100%', padding: 10, marginBottom: 16, borderRadius: 6, background: '#0f172a', color: '#e2e8f0', border: '1px solid #475569' }}
              />
              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                <button type="button" className="btn secondary" onClick={() => { setClearModal(null); setClearConfirmText('') }} disabled={clearing}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn"
                  style={{ background: clearConfirmText === 'DELETE' ? '#dc2626' : '#475569', cursor: clearConfirmText === 'DELETE' ? 'pointer' : 'not-allowed' }}
                  onClick={handleClear}
                  disabled={clearing || clearConfirmText !== 'DELETE'}
                >
                  {clearing ? 'Clearing...' : 'Clear'}
                </button>
              </div>
            </div>
          </div>
        )
      }
      {loading && <p>Loading...</p>}
      {
        !loading && sortedResidents.length > 0 && (
          <div className="schedule-scroll-outer">
            <div
              ref={scrollTopRef}
              className="schedule-scroll-bar-top"
              onScroll={() => syncScroll('top')}
              aria-label="Horizontal scroll"
            >
              <div className="schedule-scroll-spacer" style={{ width: 52 * 60 + 340 }} />
            </div>
            <div
              ref={scrollMainRef}
              className="schedule-excel-wrapper"
              onScroll={() => syncScroll('main')}
            >
              <table className="schedule-excel-table" style={{ tableLayout: 'fixed', width: 52 * 60 + 340 }}>
                <thead>
                  <tr className="schedule-block-row">
                    <th rowSpan={2} className="schedule-th-clear" style={{ width: 40, minWidth: 40 }} />
                    <th rowSpan={2} className="schedule-th-cohort" style={{ width: 80, minWidth: 80 }}>Cohort</th>
                    <th rowSpan={2} className="schedule-th-pgy" style={{ width: 60, minWidth: 60 }}>PGY</th>
                    <th rowSpan={2} className="schedule-th-name" style={{ width: 160, minWidth: 160 }}>Name</th>
                    {blocks.map((b, i) => (
                      <th key={i} colSpan={b.colspan} className="schedule-th-block">
                        {b.label}
                      </th>
                    ))}
                  </tr>
                  <tr className="schedule-week-row">
                    {Array.from({ length: 52 }, (_, i) => (
                      <th
                        key={i}
                        className={`schedule-th-week ${blockEdges.has(i + 1) ? 'block-edge' : ''}`}
                        style={{ width: 60, minWidth: 60 }}
                      >
                        {getWeekSpan(i + 1, startDate)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedResidents.map((r, idx) => {
                    const meta = rowMeta[idx] || {}
                    const pgyClass = r.pgy === 'PGY1' ? 'pgy1-row' : r.pgy === 'PGY2' ? 'pgy2-row' : r.pgy === 'PGY3' ? 'pgy3-row' : r.pgy === 'TY' ? 'ty-row' : ''
                    const cohortNum = parseInt(r.cohort_name?.match(/\d+/)?.[0] || '0', 10)
                    const cohortClass = cohortNum > 0 ? `cohort-strip-${((cohortNum - 1) % 3) + 1}` : ''

                    return (
                      <tr
                        key={r.id}
                        className={`schedule-resident-row ${pgyClass} ${cohortClass} ${meta.isFirstInCohort ? 'schedule-cohort-divider' : ''} ${meta.isFirstInPgy ? 'schedule-pgy-divider' : ''}`}
                      >
                        <td className="schedule-td-clear">
                          {countRotationsForResident(r.id) > 0 && (
                            <button
                              type="button"
                              className="schedule-clear-btn"
                              title="Clear schedule"
                              onClick={(e) => { e.stopPropagation(); setClearModal({ type: 'resident', resident: { id: r.id, name: r.name } }); setClearConfirmText('') }}
                            >
                              −
                            </button>
                          )}
                        </td>
                        <td className="schedule-td-cohort" style={{ fontSize: '10px' }}>{r.pgy === 'TY' ? (r.track ? r.track.charAt(0).toUpperCase() + r.track.slice(1) : 'TY') : (r.cohort_name ?? '—')}</td>
                        <td className="schedule-td-pgy" style={{ fontSize: '10px' }}>{r.pgy}</td>
                        <td className="schedule-td-name">{r.name}</td>
                        {Array.from({ length: 52 }, (_, i) => {
                          const week = i + 1
                          const code = (assignments[r.id] || {})[week] || ''
                          const bg = code ? (ROT_COLORS[code] ?? '#334155') : undefined
                          const isEditing = editingCell?.residentId === r.id && editingCell?.week === week
                          return (
                            <td
                              key={i}
                              className={`schedule-td-rot ${blockEdges.has(i + 1) ? 'block-edge' : ''}`}
                              style={{ backgroundColor: bg }}
                            >
                              {isEditing ? (
                                <select
                                  value={code}
                                  autoFocus
                                  onChange={(e) => updateCell(r.id, week, e.target.value)}
                                  onBlur={() => setEditingCell(null)}
                                  onClick={(e) => e.stopPropagation()}
                                  disabled={savingCell}
                                  style={{
                                    width: '100%',
                                    minWidth: 40,
                                    fontSize: '9px',
                                    background: '#1e293b',
                                    color: '#e2e8f0',
                                    padding: 0
                                  }}
                                >
                                  {ROT_OPTIONS.map((opt) => (
                                    <option key={opt || 'blank'} value={opt}>
                                      {opt ? rotLabel(opt) : '—'}
                                    </option>
                                  ))}
                                </select>
                              ) : (
                                <span
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setEditingCell({ residentId: r.id, week })
                                  }}
                                  style={{ cursor: 'pointer', display: 'block', minHeight: 18, textAlign: 'center' }}
                                >
                                  {code ? rotLabel(code) : '·'}
                                </span>
                              )}
                            </td>
                          )
                        })}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div
              ref={scrollBottomRef}
              className="schedule-scroll-bar-bottom"
              onScroll={() => syncScroll('bottom')}
              aria-label="Horizontal scroll bottom"
            >
              <div className="schedule-scroll-spacer" style={{ width: 52 * 60 + 340 }} />
            </div>
          </div>
        )
      }
      {
        !loading && sortedResidents.length === 0 && (
          <p>
            {searchResident.trim() || filterPgy || filterRot
              ? 'No residents match your search or filters. Try clearing them.'
              : 'No residents or no schedule yet. Generate first.'}
          </p>
        )
      }
      {
        remaining.length > 0 && (
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 32 }}>
            <div style={{ flex: '1 1 600px', minWidth: 300 }}>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, fontSize: '1.25rem' }}>
                📊 Rotation Counts
              </h2>
              <div style={{ maxHeight: 300, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 8, background: 'white' }}>
                <table className="stats-table" style={{ fontSize: '0.75rem' }}>
                  <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                    <tr>
                      <th style={{ background: '#f8fafc' }}>Resident</th>
                      <th style={{ background: '#f8fafc' }}>Track</th>
                      <th style={{ background: '#f8fafc' }}>PGY</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>Flr</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>ICU</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>ICUN</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>NF</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>Swn</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>Core</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedResidents.map((r) => {
                      const wks = assignments[r.id] || {}
                      const wVals = Object.values(wks)
                      const floors = wVals.filter(v => ['A', 'B', 'C', 'D', 'G'].includes(v)).length
                      const icu = wVals.filter(v => ['ICU'].includes(v)).length
                      const icun = wVals.filter(v => ['ICU N'].includes(v)).length
                      const nf = wVals.filter(v => ['NF'].includes(v)).length
                      const swing = wVals.filter(v => ['SWING'].includes(v)).length
                      const core = wVals.filter(v => ['CARDIO', 'ID', 'NEURO', 'GERIATRICS', 'ED', 'GEN SURG'].includes(v)).length
                      const trackInfo = r.pgy === 'TY' ? (r.track ? r.track.charAt(0).toUpperCase() + r.track.slice(1) : '—') : (r.cohort_name ?? r.cohort_id ?? '—')

                      return (
                        <tr key={r.id} style={{ background: 'white' }}>
                          <td style={{ fontWeight: 500, fontSize: '0.85rem' }}>{r.name}</td>
                          <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{trackInfo}</td>
                          <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{r.pgy}</td>
                          <td style={{ textAlign: 'center', background: floors > 0 ? 'rgba(134, 239, 172, 0.05)' : 'white', color: floors > 0 ? '#86efac' : '#475569', fontWeight: floors > 0 ? 600 : 400 }}>{floors}</td>
                          <td style={{ textAlign: 'center', background: icu > 0 ? 'rgba(125, 211, 252, 0.05)' : 'white', color: icu > 0 ? '#7dd3fc' : '#475569', fontWeight: icu > 0 ? 600 : 400 }}>{icu}</td>
                          <td style={{ textAlign: 'center', background: icun > 0 ? 'rgba(56, 189, 248, 0.05)' : 'white', color: icun > 0 ? '#38bdf8' : '#475569', fontWeight: icun > 0 ? 600 : 400 }}>{icun}</td>
                          <td style={{ textAlign: 'center', background: nf > 0 ? 'rgba(226, 232, 240, 0.05)' : 'white', color: nf > 0 ? '#e2e8f0' : '#475569', fontWeight: nf > 0 ? 600 : 400 }}>{nf}</td>
                          <td style={{ textAlign: 'center', background: swing > 0 ? 'rgba(196, 181, 253, 0.05)' : 'white', color: swing > 0 ? '#c4b5fd' : '#475569', fontWeight: swing > 0 ? 600 : 400 }}>{swing}</td>
                          <td style={{ textAlign: 'center', background: core > 0 ? 'rgba(253, 186, 116, 0.05)' : 'white', color: core > 0 ? '#fdba74' : '#475569', fontWeight: core > 0 ? 600 : 400 }}>{core}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ flex: '1 1 400px', minWidth: 300 }}>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, fontSize: '1.25rem' }}>
                🚩 Deficits
              </h2>
              <div className="remaining-requirements-scroll" style={{ maxHeight: 300, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 8, background: 'white' }}>
                <table style={{ fontSize: '0.75rem' }}>
                  <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                    <tr>
                      <th style={{ background: '#f8fafc' }}>Resident</th>
                      <th style={{ background: '#f8fafc' }}>Category</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>R</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>D</th>
                      <th style={{ background: '#f8fafc', textAlign: 'center' }}>L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {remaining.filter((r) => r.remaining > 0).map((r, i) => (
                      <tr key={i} style={{ background: 'white' }}>
                        <td style={{ fontSize: '0.85rem' }}>{r.resident_name}</td>
                        <td style={{ fontSize: '0.85rem' }}>{r.category}</td>
                        <td style={{ textAlign: 'center', fontSize: '0.85rem' }}>{r.required}</td>
                        <td style={{ textAlign: 'center', fontSize: '0.85rem' }}>{r.completed}</td>
                        <td style={{ textAlign: 'center', color: '#fca5a5', fontWeight: 600, fontSize: '0.85rem' }}>{r.remaining}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )
      }
      <p style={{ marginTop: 24, fontSize: '0.85rem', color: '#94a3b8', borderTop: '1px solid #3d424d', paddingTop: 16 }}>
        <strong>Legend:</strong> Green = Floors (A-G) | Blue = ICU/Surgery | Red/Pink = Vacation | Orange/Yellow = Subspecialties | Purple = Swing | Gray = NF
      </p>
    </div >
  )
}
