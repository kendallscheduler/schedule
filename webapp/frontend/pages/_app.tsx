import type { AppProps } from 'next/app'
import Link from 'next/link'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-logo" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <img src="/kendall_logo.jpg" alt="Logo" style={{ width: 28, height: 28, borderRadius: '4px' }} />
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
