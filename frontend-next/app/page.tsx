import Link from 'next/link';

export default function Home() {
  return (
    <main style={{padding: 24}}>
      <h1>Comparative Coaching – Expert Tools</h1>
      <ul>
        <li><Link href="/expert">Expert Home</Link></li>
        <li><Link href="/expert/label">Label Queue</Link></li>
        <li><Link href="/expert/metrics">Metrics</Link></li>
        <li><Link href="/user/settings">User Settings</Link></li>
      </ul>
    </main>
  );
}

