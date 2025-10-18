"use client";
import React from 'react';
import type { Pair } from '../lib/api';

function redactEmails(s: string) {
  return s.replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, '[email]');
}

export default function PairCard({ pair, onPick }: { pair: Pair; onPick: (w: 'A'|'B'|'ABSTAIN') => void }) {
  const a = pair.a, b = pair.b;
  return (
    <div className="card">
      <div className="row"><span className="pill">Goal: {pair.context?.goal}</span></div>
      <div className="grid">
        <div>
          <div><strong>A: {redactEmails(a.subject)}</strong></div>
          <div style={{whiteSpace:'pre-wrap', maxHeight: 220, overflow:'auto'}}>{redactEmails(a.body)}</div>
          <button onClick={()=>onPick('A')} aria-label="Pick A (left)">Pick A</button>
        </div>
        <div>
          <div><strong>B: {redactEmails(b.subject)}</strong></div>
          <div style={{whiteSpace:'pre-wrap', maxHeight: 220, overflow:'auto'}}>{redactEmails(b.body)}</div>
          <button onClick={()=>onPick('B')} aria-label="Pick B (right)">Pick B</button>
        </div>
      </div>
      <div className="row" style={{justifyContent:'space-between'}}>
        <button onClick={()=>onPick('ABSTAIN')} className="pill" aria-label="Abstain">Abstain</button>
      </div>
    </div>
  );
}

