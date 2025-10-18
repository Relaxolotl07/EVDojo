"use client";
import React from 'react';
import TopicSelect from '../../../components/TopicSelect';
import { api } from '../../../lib/api';

export default function UserSettings() {
  const [topic, setTopic] = React.useState<string>('internal-request');
  const [current, setCurrent] = React.useState<string | null>(null);
  React.useEffect(()=>{ api.get(`/users/me`).then(d => { setCurrent(d.preferred_topic); if (d.preferred_topic) setTopic(d.preferred_topic); }).catch(()=>{}); }, []);
  async function save() {
    await api.post(`/users/me/topic`, { topic });
    setCurrent(topic);
  }
  return (
    <main style={{padding:24}}>
      <h2>User Settings</h2>
      <div className="row"><span>Preferred topic</span> <TopicSelect value={topic} onChange={setTopic} /> <button onClick={save}>Save</button></div>
      <div className="row">Current: {current || 'none'}</div>
      <div className="row">Your sessions will default to {topic}.</div>
    </main>
  );
}

