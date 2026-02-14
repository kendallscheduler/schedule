import type { AppProps } from 'next/app'
import Link from 'next/link'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          Kendall Scheduler
        </div>
        <Link href="/">Home</Link>
        <Link href="/residents">Residents</Link>
        <Link href="/requirements">Requirements</Link>
        <Link href="/schedule">Schedule</Link>
        <Link href="/rollover">Rollover</Link>
        <Link href="/generate">Generate</Link>
      </nav>
      <main className="main">
        <Component {...pageProps} />
      </main>
    </div>
  )
}
