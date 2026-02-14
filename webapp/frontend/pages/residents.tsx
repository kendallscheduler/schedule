import React, { useEffect, useState, useMemo } from 'react'
import { api } from '../lib/api'

const API = '' // Same-origin; Next.js proxies /api/* to backend

type RemainingRow = {
  resident_id: number
  resident_name: string
  pgy: string
  category: string
  required: number
  completed: number
  remaining: number
}

export default function ResidentsPage() {
  const [years, setYears] = useState<{ id: number; name: string }[]>([])
  const [residents, setResidents] = useState<any[]>([])
  const [remaining, setRemaining] = useState<RemainingRow[]>([])
  const [yearId, setYearId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [newPgy, setNewPgy] = useState('PGY1')
  const [newTrack, setNewTrack] = useState<string>('')
  const [newCohortId, setNewCohortId] = useState<number | ''>('')
  const [cohorts, setCohorts] = useState<{ id: number; name: string }[]>([])
  const [yearsError, setYearsError] = useState<string | null>(null)
  const [newYearName, setNewYearName] = useState('2026-2027')
  const [completionsByResident, setCompletionsByResident] = useState<Record<number, { category: string; completed_weeks: number }[]>>({})
  const [rotationHistoryByResident, setRotationHistoryByResident] = useState<Record<number, { year_name: string; pgy: string; assignments: { week: number; rotation: string }[]; by_category?: Record<string, number> }[]>>({})
  const [editingDone, setEditingDone] = useState<{ residentId: number; category: string } | null>(null)
  const [doneWeeks, setDoneWeeks] = useState('')
  const [savingDone, setSavingDone] = useState(false)
  const [sortBy, setSortBy] = useState<'name' | 'pgy' | 'cohort'>('pgy')
  const [pasteScheduleText, setPasteScheduleText] = useState('')
  const [pastingSchedule, setPastingSchedule] = useState(false)
  const [vacationByResident, setVacationByResident] = useState<Record<number, { block_a_option1_start: number | null; block_a_option2_start: number | null; block_b_option1_start: number | null; block_b_option2_start: number | null }>>({})
  const [vacationEdit, setVacationEdit] = useState<{ a1: string; a2: string; b1: string; b2: string } | null>(null)
  const [savingVacation, setSavingVacation] = useState(false)
  const [editingNameId, setEditingNameId] = useState<number | null>(null)
  const [editingNameValue, setEditingNameValue] = useState('')
  const [savingName, setSavingName] = useState(false)

  useEffect(() => {
    api.years()
      .then((y) => {
        const list = Array.isArray(y) ? y : []
        setYears(list)
        setYearsError(null)
        if (list[0]) setYearId(list[0].id)
      })
      .catch((e) => {
        setYearsError(e?.message || 'Failed to load years. Is the backend running?')
        setYears([])
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!yearId) {
      setResidents([])
      setRemaining([])
      return
    }
    api.cohorts(yearId).then(setCohorts).catch(() => setCohorts([]))
    Promise.all([api.residents(yearId), api.remaining(yearId)])
      .then(([res, rem]) => {
        setResidents(res ?? [])
        setRemaining(rem ?? [])
      })
      .catch((e) => {
        console.error(e)
        setResidents([])
        setRemaining([])
      })
  }, [yearId])

  const remainingByResident = useMemo(() => {
    const by: Record<number, RemainingRow[]> = {}
    for (const row of remaining) {
      if (!by[row.resident_id]) by[row.resident_id] = []
      by[row.resident_id].push(row)
    }
    return by
  }, [remaining])

  const sortedResidents = useMemo(() => {
    const arr = [...residents]
    const pgyOrder: Record<string, number> = { PGY1: 0, PGY2: 1, PGY3: 2, TY: 3 }
    if (sortBy === 'name') {
      arr.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    } else if (sortBy === 'pgy') {
      arr.sort((a, b) => {
        const pa = pgyOrder[a.pgy] ?? 99
        const pb = pgyOrder[b.pgy] ?? 99
        if (pa !== pb) return pa - pb
        return (a.name || '').localeCompare(b.name || '')
      })
    } else {
      arr.sort((a, b) => {
        const ca = String(a.cohort_name ?? a.cohort_id ?? '')
        const cb = String(b.cohort_name ?? b.cohort_id ?? '')
        const cmp = ca.localeCompare(cb, undefined, { numeric: true })
        if (cmp !== 0) return cmp
        const pa = pgyOrder[a.pgy] ?? 99
        const pb = pgyOrder[b.pgy] ?? 99
        if (pa !== pb) return pa - pb
        return (a.name || '').localeCompare(b.name || '')
      })
    }
    return arr
  }, [residents, sortBy])

  useEffect(() => {
    if (expandedId && yearId) {
      api.completions(expandedId)
        .then((list) => setCompletionsByResident((prev) => ({ ...prev, [expandedId]: list })))
        .catch(() => { })
      api.rotationHistory(expandedId)
        .then(({ history }) => setRotationHistoryByResident((prev) => ({ ...prev, [expandedId]: history })))
        .catch(() => setRotationHistoryByResident((prev) => ({ ...prev, [expandedId]: [] })))
      api.getResidentVacationRequests(expandedId, yearId)
        .then((v) => {
          setVacationByResident((prev) => ({ ...prev, [expandedId]: v }))
          setVacationEdit(null)
        })
        .catch(() => setVacationEdit(null))
    }
  }, [expandedId, yearId])

  function getPriorWeeks(residentId: number, category: string): number {
    const list = completionsByResident[residentId] || []
    const c = list.find((x) => x.category === category)
    return c?.completed_weeks ?? 0
  }

  async function saveDone(residentId: number, category: string, newDone: number, currentCompleted: number, priorWeeks: number) {
    if (!yearId) return
    setSavingDone(true)
    setMsg(null)
    const scheduleContrib = currentCompleted - priorWeeks
    const completionWeeks = scheduleContrib > 0 ? newDone : newDone - scheduleContrib
    try {
      await api.upsertCompletion({
        resident_id: residentId,
        category,
        completed_weeks: scheduleContrib > 0 ? newDone : completionWeeks,
        year_id: yearId,
      })
      const [completionsList, rem] = await Promise.all([
        api.completions(residentId),
        api.remaining(yearId),
      ])
      setCompletionsByResident((prev) => ({ ...prev, [residentId]: completionsList }))
      setRemaining(rem)
      setEditingDone(null)
      setMsg('Saved. Schedule grid updated.')
      if (typeof window !== 'undefined') window.localStorage.setItem('schedule-invalidated', String(Date.now()))
    } catch (e: any) {
      const errMsg = e?.message || e?.toString?.() || 'Could not save'
      setMsg(`Error: ${errMsg}`)
    } finally {
      setSavingDone(false)
    }
  }

  async function saveName(residentId: number, newName: string) {
    if (!newName.trim() || savingName) return setEditingNameId(null)
    setSavingName(true)
    try {
      await api.updateResident(residentId, { name: newName.trim() })
      const res = await api.residents(yearId!)
      setResidents(res)
      setEditingNameId(null)
      setMsg('Name updated.')
    } catch (e: any) {
      setMsg(`Error: ${e.message}`)
    } finally {
      setSavingName(false)
    }
  }

  async function doImport() {
    if (!file || !yearId) return
    setImporting(true)
    setMsg(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const resp = await fetch(`${API}/api/residents/import?year_id=${yearId}`, {
        method: 'POST',
        body: fd,
      })
      const data = await resp.json()
      if (!resp.ok) {
        const err = Array.isArray(data.detail) ? data.detail.map((x: any) => x.msg || JSON.stringify(x)).join('; ') : (data.detail || JSON.stringify(data))
        setMsg(`Error: ${err}`)
        return
      }
      const assignStr = data.assignments != null ? ` and ${data.assignments} schedule assignments` : ''
      setMsg(`Imported ${data.created} residents${assignStr}`)
      const [residentsData, remainingData] = await Promise.all([api.residents(yearId), api.remaining(yearId)])
      setResidents(residentsData)
      setRemaining(remainingData)
    } catch (e: any) {
      setMsg(`Error: ${e.message}`)
    } finally {
      setImporting(false)
    }
  }

  return (
    <div style={{ paddingBottom: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Residents</h1>
          <p style={{ color: '#64748b', fontSize: '0.8125rem', margin: 0 }}>
            Manage roster and progress.
          </p>
        </div>
        <div className="card" style={{ padding: '0.4rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Year</label>
          <select
            value={yearId ?? ''}
            onChange={(e) => setYearId(e.target.value ? Number(e.target.value) : null)}
            style={{ width: 110, border: 'none', background: 'transparent', fontWeight: 600, fontSize: '0.8125rem', cursor: 'pointer' }}
          >
            <option value="">Select...</option>
            {years.map((y) => (
              <option key={y.id} value={y.id}>{y.name}</option>
            ))}
          </select>
        </div>
      </div>

      {msg && (
        <div className={`alert ${msg.startsWith('Error') ? 'error' : 'success'}`} style={{ marginBottom: '1rem', padding: '0.5rem 1rem', fontSize: '0.8125rem' }}>
          {msg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem' }}>
            <h5 style={{ margin: 0, fontSize: '0.875rem' }}>Import</h5>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div style={{ flex: 1, border: '1px dashed #e2e8f0', padding: '0.4rem', borderRadius: '6px', textAlign: 'center', cursor: 'pointer', overflow: 'hidden' }} onClick={() => document.getElementById('fileInput')?.click()}>
              <input id="fileInput" type="file" accept=".xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} style={{ display: 'none' }} />
              <span style={{ fontSize: '0.7rem', color: file ? '#0f172a' : '#94a3b8', whiteSpace: 'nowrap' }}>
                {file ? file.name : 'Choose Excel'}
              </span>
            </div>
            <button className="btn" onClick={doImport} disabled={!file || !yearId || importing} style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
              {importing ? '...' : 'Sync'}
            </button>
          </div>
        </div>

        <div className="card" style={{ padding: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem' }}>
            <h5 style={{ margin: 0, fontSize: '0.875rem' }}>Add Resident</h5>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 0.6fr 0.4fr', gap: '0.4rem' }}>
            <input placeholder="Name" value={newName} onChange={(e) => setNewName(e.target.value)} style={{ padding: '2px 6px', fontSize: '0.8125rem' }} />
            <select value={newPgy} onChange={(e) => { setNewPgy(e.target.value); if (e.target.value !== 'TY') setNewTrack('') }} style={{ padding: '2px 4px', fontSize: '0.8125rem' }}>
              <option value="PGY1">PGY1</option><option value="PGY2">PGY2</option><option value="PGY3">PGY3</option><option value="TY">TY</option>
            </select>
            <button className="btn" disabled={!newName.trim()} style={{ padding: '2px' }} onClick={async () => {
              try {
                await api.createResident({ name: newName.trim(), pgy: newPgy, year_id: yearId! });
                setNewName(''); setMsg('Added.'); const [res, rem] = await Promise.all([api.residents(yearId!), api.remaining(yearId!)]); setResidents(res); setRemaining(rem);
              } catch (e: any) { setMsg(`Error: ${e.message}`) }
            }}>Add</button>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h2 style={{ margin: 0, fontSize: '1rem' }}>Roster</h2>
          <span style={{ padding: '1px 6px', background: '#f1f5f9', color: '#64748b', borderRadius: '10px', fontSize: '0.65rem', fontWeight: 600 }}>{residents.length}</span>
        </div>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as 'name' | 'pgy' | 'cohort')} style={{ padding: '1px 6px', fontSize: '0.75rem', borderRadius: '4px' }}>
          <option value="name">Sort: Name</option><option value="pgy">Sort: PGY</option><option value="cohort">Sort: Cohort</option>
        </select>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ margin: 0, fontSize: '0.8125rem' }}>
          <thead>
            <tr>
              <th style={{ width: 28 }}></th>
              <th>Name</th>
              <th>PGY</th>
              <th>Track</th>
              <th>Cohort</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {sortedResidents.length === 0 && (
              <tr><td colSpan={7} style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No residents found</td></tr>
            )}
            {sortedResidents.map((r, idx) => {
              const resRemaining = remainingByResident[r.id] || []
              const isExpanded = expandedId === r.id
              const cohortNum = parseInt(r.cohort_name?.match(/\d+/)?.[0] || '0', 10)
              const cohortClass = cohortNum > 0 ? `cohort-strip-${((cohortNum - 1) % 3) + 1}` : ''
              const isFirstInCohort = sortBy === 'cohort' && (idx === 0 || r.cohort_name !== sortedResidents[idx - 1].cohort_name)
              const pgyClass = r.pgy === 'PGY1' ? 'pgy1-row' : r.pgy === 'PGY2' ? 'pgy2-row' : r.pgy === 'PGY3' ? 'pgy3-row' : r.pgy === 'TY' ? 'ty-row' : ''

              return (
                <React.Fragment key={r.id}>
                  {isFirstInCohort && idx > 0 && (
                    <tr className="schedule-cohort-divider"><td colSpan={7} style={{ height: 4, padding: 0, background: '#cbd5e1' }} /></tr>
                  )}
                  <tr onClick={() => setExpandedId(isExpanded ? null : r.id)} style={{ cursor: 'pointer', backgroundColor: isExpanded ? '#f8fafc' : 'transparent' }} className={`${pgyClass} ${cohortClass}`}>
                    <td style={{ textAlign: 'center', color: '#cbd5e1', fontSize: '0.6rem' }}>{isExpanded ? '▼' : '▶'}</td>
                    <td onClick={(e) => { e.stopPropagation(); setEditingNameId(r.id); setEditingNameValue(r.name) }}>
                      {editingNameId === r.id ? (
                        <input
                          autoFocus
                          value={editingNameValue}
                          onChange={(e) => setEditingNameValue(e.target.value)}
                          onBlur={() => saveName(r.id, editingNameValue)}
                          onKeyDown={(e) => e.key === 'Enter' && saveName(r.id, editingNameValue)}
                          style={{ fontSize: '0.8125rem', width: '100%', padding: '0 4px' }}
                        />
                      ) : (
                        <span style={{ borderBottom: '1px dashed #cbd5e1' }}>{r.name}{r.is_placeholder ? ' ⬚' : ''}</span>
                      )}
                    </td>
                    <td>{r.pgy}</td>
                    <td>
                      {r.pgy === 'TY'
                        ? (r.track === 'anesthesia' ? 'Anesthesia' : r.track === 'neurology' ? 'Neurology' : 'TY')
                        : '—'
                      }
                    </td>
                    <td className="schedule-td-cohort">{r.cohort_name ?? '—'}</td>
                    <td><div style={{ display: 'flex', gap: '2px' }}>{r.is_senior && <div style={{ width: 5, height: 5, borderRadius: '50%', background: '#3b82f6' }} />}{r.is_intern && <div style={{ width: 5, height: 5, borderRadius: '50%', background: '#10b981' }} />}</div></td>
                    <td style={{ textAlign: 'right' }}><button className="btn secondary" style={{ padding: '1px 4px', fontSize: '0.65rem' }}>{isExpanded ? 'Hide' : 'Info'}</button></td>
                  </tr>
                  {isExpanded && (
                    <tr key={`${r.id}-detail`}>
                      <td colSpan={7} style={{ padding: '0.75rem', backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1rem' }}>
                          <div>
                            <h6 style={{ margin: '0 0 0.4rem 0', fontSize: '0.65rem', color: '#64748b', textTransform: 'uppercase' }}>Requirements</h6>
                            <table style={{ margin: 0, fontSize: '0.7rem' }}>
                              <thead><tr><th>Category</th><th>Goal</th><th>Done</th><th style={{ textAlign: 'right' }}>Left</th></tr></thead>
                              <tbody>
                                {resRemaining.map(row => (
                                  <tr key={row.category}>
                                    <td>{row.category}</td><td>{row.required}w</td>
                                    <td>{editingDone?.residentId === r.id && editingDone?.category === row.category ? <input type="number" value={doneWeeks} autoFocus style={{ width: 30 }} onChange={e => setDoneWeeks(e.target.value)} onBlur={() => saveDone(r.id, row.category, parseInt(doneWeeks, 10), row.completed, getPriorWeeks(r.id, row.category))} /> : <span onClick={() => { setEditingDone({ residentId: r.id, category: row.category }); setDoneWeeks(String(row.completed)) }} style={{ cursor: 'pointer', textDecoration: 'underline' }}>{row.completed}</span>}</td>
                                    <td style={{ textAlign: 'right', fontWeight: 600, color: row.remaining > 0 ? '#f59e0b' : '#10b981' }}>{row.remaining > 0 ? row.remaining + 'w' : '✓'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <div>
                            {r.pgy === 'TY' && (
                              <>
                                <h6 style={{ margin: '0 0 0.4rem 0', fontSize: '0.65rem', color: '#64748b', textTransform: 'uppercase' }}>Track Selection</h6>
                                <select value={r.track || ''} onChange={async (e) => { try { await api.updateResident(r.id, { track: e.target.value || undefined }); const [res, rem] = await Promise.all([api.residents(yearId!), api.remaining(yearId!)]); setResidents(res); setRemaining(rem); } catch (e: any) { setMsg(e.message) } }} style={{ fontSize: '0.75rem', width: '100%', marginBottom: '0.75rem' }}>
                                  <option value="">General TY</option><option value="anesthesia">Anesthesia</option><option value="neurology">Neurology</option>
                                </select>
                              </>
                            )}

                            <h6 style={{ margin: '0 0 0.4rem 0', fontSize: '0.65rem', color: '#64748b', textTransform: 'uppercase' }}>Vacation Week Requests (1-52)</h6>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '0.55rem', color: '#94a3b8' }}>Block A Opt 1</label>
                                <input type="number" placeholder="Wk" value={vacationEdit ? (vacationEdit as any).a1 : String((vacationByResident[r.id] as any)?.block_a_option1_start ?? '')} onChange={e => setVacationEdit((prev: any) => ({ ...(prev || {}), a1: e.target.value }))} style={{ padding: '2px', fontSize: '0.75rem' }} />
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '0.55rem', color: '#94a3b8' }}>Block A Opt 2</label>
                                <input type="number" placeholder="Wk" value={vacationEdit ? (vacationEdit as any).a2 : String((vacationByResident[r.id] as any)?.block_a_option2_start ?? '')} onChange={e => setVacationEdit((prev: any) => ({ ...(prev || {}), a2: e.target.value }))} style={{ padding: '2px', fontSize: '0.75rem' }} />
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '0.55rem', color: '#94a3b8' }}>Block B Opt 1</label>
                                <input type="number" placeholder="Wk" value={vacationEdit ? (vacationEdit as any).b1 : String((vacationByResident[r.id] as any)?.block_b_option1_start ?? '')} onChange={e => setVacationEdit((prev: any) => ({ ...(prev || {}), b1: e.target.value }))} style={{ padding: '2px', fontSize: '0.75rem' }} />
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <label style={{ fontSize: '0.55rem', color: '#94a3b8' }}>Block B Opt 2</label>
                                <input type="number" placeholder="Wk" value={vacationEdit ? (vacationEdit as any).b2 : String((vacationByResident[r.id] as any)?.block_b_option2_start ?? '')} onChange={e => setVacationEdit((prev: any) => ({ ...(prev || {}), b2: e.target.value }))} style={{ padding: '2px', fontSize: '0.75rem' }} />
                              </div>
                            </div>
                            <button className="btn secondary" style={{ width: '100%', fontSize: '0.65rem', padding: '2px' }} onClick={async () => {
                              if (!yearId || !vacationEdit) return; setSavingVacation(true); try { const p = (s: string) => parseInt(s, 10) || undefined; await api.upsertResidentVacationRequests({ resident_id: r.id, year_id: yearId, block_a_option1_start: p(vacationEdit.a1), block_a_option2_start: p(vacationEdit.a2), block_b_option1_start: p(vacationEdit.b1), block_b_option2_start: p(vacationEdit.b2) }); const v = await api.getResidentVacationRequests(r.id, yearId); setVacationByResident(prev => ({ ...prev, [r.id]: v })); setVacationEdit(null); setMsg('Saved.'); } catch (e: any) { setMsg(e.message) } finally { setSavingVacation(false) }
                            }}>Save Requests</button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
