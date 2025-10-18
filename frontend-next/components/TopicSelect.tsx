"use client";
import React from 'react';
import { api } from '../lib/api';

export default function TopicSelect({ value, onChange }: { value?: string; onChange: (v: string) => void }) {
  const [topics, setTopics] = React.useState<string[]>([]);
  React.useEffect(() => { api.get<{topics:string[]}>(`/topics`).then(d => setTopics(d.topics)).catch(()=>{}); }, []);
  return (
    <select value={value} onChange={(e)=>onChange(e.target.value)} aria-label="Topic selector">
      {topics.map(t => <option key={t} value={t}>{t}</option>)}
    </select>
  );
}

