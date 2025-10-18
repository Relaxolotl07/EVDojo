"use client";
import React from 'react';
import { api } from '../lib/api';

export default function CSVUpload({ topic }: { topic: string }) {
  const [file, setFile] = React.useState<File | null>(null);
  const [preview, setPreview] = React.useState<string[][]>([]);
  const [result, setResult] = React.useState<any>(null);

  async function handleFile(f: File) {
    setFile(f);
    const text = await f.text();
    const rows = text.split(/\r?\n/).slice(0, 11).map(r => r.split(','));
    setPreview(rows);
  }

  async function importCsv() {
    if (!file) return;
    const fd = new FormData();
    fd.append('topic', topic);
    fd.append('csv_file', file);
    const resp = await api.postForm<any>(`/import/emails`, fd);
    setResult(resp);
  }

  async function loadSample() {
    try {
      const res = await fetch('/emails.csv');
      const blob = await res.blob();
      const f = new File([blob], 'emails.csv', { type: 'text/csv' });
      await handleFile(f);
    } catch (e) { /* ignore */ }
  }

  return (
    <div className="card">
      <div className="row">
        <input type="file" accept=".csv" onChange={(e)=> e.target.files && handleFile(e.target.files[0])} />
        <button onClick={loadSample} title="Load sample emails.csv">Load sample</button>
        <span className="pill">Topic: {topic || '—'}</span>
      </div>
      {preview.length>0 && (
        <div>
          <div className="row"><strong>Preview (first 10 rows)</strong></div>
          <div className="card" style={{maxHeight: 240, overflow:'auto'}}>
            <table style={{width:'100%', fontSize:12}}>
              <tbody>
                {preview.map((r,i)=> (
                  <tr key={i}>{r.map((c,j)=>(<td key={j} style={{borderBottom:'1px solid #2a3249', padding: '4px'}}>{c}</td>))}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <button onClick={importCsv} disabled={!file}>Import</button>
        </div>
      )}
      {result && <div className="row">Imported items: {result.count_items} · pairs: {result.count_pairs}</div>}
    </div>
  );
}
