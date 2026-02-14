import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function VacationsPage() {
  const [years, setYears] = useState<{ id: number; name: string }[]>([])
  const [residents, setResidents] = useState<any[]>([])
  const [vacations, setVacations] = useState<any[]>([])
  const [yearId, setYearId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.years().then((y) => { setYears(y); if (y[0]) setYearId(y[0].id); }).catch(console.error).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (yearId) {
      api.residents(yearId).then(setResidents)
      api.vacations(yearId).then(setVacations)
    }
  }, [yearId])

  const resByName = Object.fromEntries(residents.map((r) => [r.id, r.name]))

  return (
    <div>
      <h1>Vacation Requests</h1>
      <div className="form-group">
        <label>Year</label>
        <select value={yearId || ''} onChange={(e) => setYearId(Number(e.target.value))}>
          {years.map((y) => (
            <option key={y.id} value={y.id}>{y.name}</option>
          ))}
        </select>
      </div>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
        Add vacation requests via API (POST /api/vacations/). Each resident needs 4 weeks total (two 2-week blocks).
      </p>
      {loading && <p>Loading...</p>}
      <table>
        <thead>
          <tr>
            <th>Resident</th>
            <th>Block</th>
            <th>Start Week</th>
            <th>Length</th>
            <th>Priority</th>
            <th>Hard Lock</th>
          </tr>
        </thead>
        <tbody>
          {vacations.map((v) => (
            <tr key={v.id}>
              <td>{resByName[v.resident_id] ?? v.resident_id}</td>
              <td>{v.block}</td>
              <td>{v.start_week}</td>
              <td>{v.length_weeks}</td>
              <td>{v.priority}</td>
              <td>{v.hard_lock ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {vacations.length === 0 && !loading && <p>No vacation requests yet.</p>}
    </div>
  )
}
