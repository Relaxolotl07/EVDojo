"use client";
import React from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '../../../lib/api';

export default function MetricsPage() {
  const sp = useSearchParams();
  const topic = sp.get('topic') || 'internal-request';
  const [m, setM] = React.useState<any>(null);
  React.useEffect(()=>{ api.get(`/metrics/topic?topic=${encodeURIComponent(topic)}`).then(setM).catch(()=>{}); }, [topic]);
  return (
    <main style={{padding:24}}>
      <h2>Metrics – {topic}</h2>
      {m ? (
        <div className="grid">
          <div className="card">Labeled pairs<br /><strong>{m.labeled_pairs}</strong></div>
          <div className="card">κ (agreement)<br /><strong>{m.kappa}</strong></div>
          <div className="card">Abstain rate<br /><strong>{(m.abstain_rate*100).toFixed(1)}%</strong></div>
          <div className="card">RM AUC<br /><strong>{m.rm_auc}</strong></div>
        </div>
      ) : (
        <div className="card">Loading...</div>
      )}
    </main>
  );
}

