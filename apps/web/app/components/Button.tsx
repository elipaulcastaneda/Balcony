import Link from 'next/link'

export default function Button({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} style={{
      display: 'inline-block',
      padding: '8px 16px',
      background: '#0366d6',
      color: 'white',
      borderRadius: 6,
      textDecoration: 'none'
    }}>{children}</Link>
  )
}
