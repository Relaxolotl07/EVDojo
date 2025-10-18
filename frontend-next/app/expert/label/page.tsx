"use client";
import React from 'react';
import { useSearchParams } from 'next/navigation';
import { api, API_BASE, Pair } from '../../../lib/api';
import PairCard from '../../../components/PairCard';
import TagChips from '../../../components/TagChips';

export default function LabelPage() {
  const sp = useSearchParams();
  const topic = sp.get('topic') || 'internal-request';
  const [pairs, setPairs] = React.useState<Pair[]>([]);
  const [tags, setTags] = React.useState<string[]>([]);
  const [idx, setIdx] = React.useState(0);
  const [left, setLeft] = React.useState(0);

  async function load() {
    const q = await api.get<Pair[]>(`/expert/queue?topic=${encodeURIComponent(topic)}&limit=50`);
    setPairs(q);
    setIdx(0);
    setLeft(q.length);
  }
  React.useEffect(() => { load(); }, [topic]);

  async function submit(winner: 'A'|'B'|'ABSTAIN') {
    const pair = pairs[idx];
    if (!pair) return;
    const idem = crypto.randomUUID();
    await fetch(`${API_BASE}/expert/label`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idem },
      body: JSON.stringify({ pair_id: pair.pair_id, winner, tags, rater_id: 'expert_ui', confidence: 0.9 }),
    });
    setTags([]);
    setIdx(i => i + 1);
    setLeft(l => Math.max(0, l - 1));
  }

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'a') submit('A');
      if (e.key.toLowerCase() === 'b') submit('B');
      if (e.key.toLowerCase() === 't') submit('ABSTAIN');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [pairs, idx, tags]);

  const pair = pairs[idx];

  return (
    <main style={{padding:24}}>
      <div className="row"><span className="pill">Topic: {topic}</span> <span className="pill">Pairs left: {left}</span></div>
      {pair ? (
        <>
          <PairCard pair={pair} onPick={submit} />
          <div className="card"><div style={{marginBottom:8}}>Reason tags</div><TagChips value={tags} onChange={setTags} /></div>
        </>
      ) : (
        <div className="card">No pairs available. Try importing CSV on Expert Home.</div>
      )}
      <div className="row"><a href={`/expert/metrics?topic=${encodeURIComponent(topic)}`}>View metrics →</a></div>
    </main>
  );
}
