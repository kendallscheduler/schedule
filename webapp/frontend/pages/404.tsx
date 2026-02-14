import Link from 'next/link'

export default function NotFound() {
  return (
    <div style={{ padding: 24, textAlign: 'center' }}>
      <h1>404 — Page not found</h1>
      <p>That page doesn&apos;t exist. Try one of the links above or <Link href="/">go home</Link>.</p>
    </div>
  )
}
