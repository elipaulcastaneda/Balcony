import Link from 'next/link'
import Button from './components/Button'

export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Balcony QC — Procurement (MVP)</h1>
      <p>Upload procurement recommendations and review findings.</p>
      <Button href="/">Get started</Button>
    </main>
  )
}
