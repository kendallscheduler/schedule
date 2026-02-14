import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Home() {
  const [years, setYears] = useState<{ id: number; name: string }[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.years().then(setYears).catch(console.error).finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 1rem' }}>
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '3rem',
        marginBottom: '5rem',
        marginTop: '5rem',
        textAlign: 'left'
      }}>
        <img
          src="/kendall_logo.jpg"
          alt="Kendall Internal Medicine Logo"
          style={{
            width: 180,
            height: 180,
            borderRadius: '20px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            border: '1px solid #e2e8f0'
          }}
        />
        <div>
          <h1 style={{
            fontSize: '3.25rem',
            marginBottom: '0.75rem',
            background: 'linear-gradient(135deg, #0f172a 0%, #2563eb 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            lineHeight: 1.1,
            fontWeight: 800
          }}>
            Kendall Hospital<br />
            <span style={{ fontSize: '2.5rem' }}>Internal Medicine</span><br />
            <span style={{ fontSize: '2rem', opacity: 0.9 }}>Master Scheduler</span>
          </h1>
          <p style={{ fontSize: '1.125rem', color: '#64748b', maxWidth: 500, margin: 0 }}>
            Optimized residency rotations and staffing coverage powered by our AI-driven engine.
          </p>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '4rem' }}>
        <a href="/residents" className="card home-card" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem 1.5rem' }}>
          <div className="icon-wrapper" style={{ background: '#eff6ff', color: '#3b82f6', padding: '12px', borderRadius: '12px', marginBottom: '1.25rem' }}>
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Residents</h3>
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.85rem', lineHeight: 1.5 }}>Manage roster, import data, and track individual progress.</p>
        </a>

        <a href="/requirements" className="card home-card" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem 1.5rem' }}>
          <div className="icon-wrapper" style={{ background: '#f0fdf4', color: '#10b981', padding: '12px', borderRadius: '12px', marginBottom: '1.25rem' }}>
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Requirements</h3>
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.85rem', lineHeight: 1.5 }}>Define PGY targets and track core rotation needs.</p>
        </a>

        <a href="/schedule" className="card home-card" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem 1.5rem' }}>
          <div className="icon-wrapper" style={{ background: '#fff7ed', color: '#f59e0b', padding: '12px', borderRadius: '12px', marginBottom: '1.25rem' }}>
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Schedule Grid</h3>
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.85rem', lineHeight: 1.5 }}>View the master schedule with real-time updates.</p>
        </a>

        <a href="/generate" className="card home-card" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem 1.5rem' }}>
          <div className="icon-wrapper" style={{ background: '#f5f3ff', color: '#8b5cf6', padding: '12px', borderRadius: '12px', marginBottom: '1.25rem' }}>
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Generate</h3>
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.85rem', lineHeight: 1.5 }}>Run the AI solver to create rule-compliant schedules.</p>
        </a>
      </div>

      <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)', borderColor: '#bfdbfe', padding: '1.25rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 40, height: 40, background: '#3b82f6', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
          </div>
          <div>
            <h4 style={{ margin: 0, color: '#1e40af', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Current Academic Year</h4>
            <p style={{ margin: '2px 0 0 0', color: '#1e3a8a', fontWeight: 700, fontSize: '1.25rem' }}>{loading ? 'Loading...' : years[0]?.name || 'N/A'}</p>
          </div>
        </div>
        <div style={{ padding: '6px 14px', background: '#3b82f6', color: 'white', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.05em', boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)' }}>
          SYSTEM LIVE
        </div>
      </div>
    </div>
  )
}
