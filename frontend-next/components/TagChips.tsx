"use client";
import React from 'react';

const DEFAULT_TAGS = ["clearer ask","shorter","less pressure","friendlier","too vague","too long"];

export default function TagChips({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const toggle = (t: string) => {
    const set = new Set(value);
    if (set.has(t)) set.delete(t); else set.add(t);
    onChange(Array.from(set));
  };
  return (
    <div className="chips">
      {DEFAULT_TAGS.map(t => (
        <div key={t} className={`chip ${value.includes(t)?'active':''}`} onClick={()=>toggle(t)} role="checkbox" aria-checked={value.includes(t)} tabIndex={0} onKeyDown={(e)=> (e.key==='Enter'||e.key===' ') && toggle(t)}>{t}</div>
      ))}
    </div>
  );
}

