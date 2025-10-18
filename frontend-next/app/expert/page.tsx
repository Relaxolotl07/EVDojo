"use client";
import React from 'react';
import TopicSelect from '../../components/TopicSelect';
import CSVUpload from '../../components/CSVUpload';
import { api } from '../../lib/api';

export default function ExpertHome() {
  const [topic, setTopic] = React.useState<string>('Email clarity');
  const [rm, setRM] = React.useState<any>(null);

  async function initTopic() {
    const resp = await api.post(`/experts/topics/init`, { topic, description: `Init ${topic}`, tags: ["clearer ask","shorter"] });
    setRM(resp);
  }

  return (
    <main style={{padding:24}}>
      <h2>Expert Home</h2>
      <div className="row">
        <span>Topic</span>
        <input aria-label="Topic text" value={topic} onChange={(e)=>setTopic(e.target.value)} placeholder="Enter topic (e.g., Email clarity)" />
        <TopicSelect value={topic} onChange={setTopic} />
        <button onClick={initTopic}>Initialize Topic</button>
        {rm && <span className="pill">rm_version: {rm.rm_version}</span>}
      </div>
      <h3>Upload CSV</h3>
      <CSVUpload topic={topic} />
      <div className="row"><a href={`/expert/label?topic=${encodeURIComponent(topic)}`}>Start labeling →</a></div>
    </main>
  );
}
