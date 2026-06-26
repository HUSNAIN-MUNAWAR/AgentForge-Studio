"use client";

import { useEffect, useState } from "react";
import { API, getJSON, postJSON } from "../lib/api";

type Doc = { id: string; title: string; chunks: number; metadata_json: any };
type FileItem = { id: string; original_name: string; size_bytes: number };

export default function MemoryPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [query, setQuery] = useState("complaint severity recommendation");
  const [results, setResults] = useState<any[]>([]);
  const [message, setMessage] = useState("");
  async function load() { setFiles(await getJSON("/api/files")); setDocs(await getJSON("/api/memory/documents")); }
  async function upload(ev: any) {
    const file = ev.target.files?.[0]; if (!file) return;
    const body = new FormData(); body.append("file", file);
    const res = await fetch(`${API}/api/files/upload`, { method: "POST", body });
    if (!res.ok) throw new Error(await res.text());
    setMessage("File uploaded. Index it to make it searchable."); await load();
  }
  async function indexFile(id: string) { const r = await postJSON(`/api/memory/index?file_id=${id}`, {}); setMessage(`Indexed ${r.chunks} chunks with ${r.engine} search.`); await load(); }
  async function search() { setResults(await getJSON(`/api/memory/search?q=${encodeURIComponent(query)}&limit=8`)); }
  useEffect(() => { load().catch(e => setMessage(e.message)); }, []);

  return <main className="space-y-6">
    <section className="hero-card"><p className="eyebrow">Memory Manager</p><h1 className="page-title">Keyword memory search</h1><p className="page-subtitle">v2 implements practical chunking and keyword retrieval in PostgreSQL. It is honest keyword search, not pgvector yet.</p></section>
    {message && <p className="text-sm text-cyan-300">{message}</p>}
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="card space-y-4"><h2 className="section-title">Upload and index</h2><input type="file" onChange={upload} className="input" /><div className="space-y-2">{files.map(file => <div key={file.id} className="rounded-xl border border-slate-800 p-3"><div className="flex items-center justify-between"><div><b>{file.original_name}</b><p className="text-xs text-slate-500">{file.size_bytes} bytes</p></div><button onClick={() => indexFile(file.id)} className="btn-secondary">Index</button></div></div>)}</div></section>
      <section className="card space-y-4"><h2 className="section-title">Indexed documents</h2>{docs.map(doc => <div key={doc.id} className="rounded-xl border border-slate-800 p-3"><b>{doc.title}</b><p className="text-xs text-slate-500">{doc.chunks} chunks · {doc.metadata_json?.engine || "keyword"}</p></div>)}{!docs.length && <div className="empty-state">No memory documents indexed.</div>}</section>
    </div>
    <section className="card space-y-4"><h2 className="section-title">Search memory</h2><div className="flex gap-2"><input className="input" value={query} onChange={e => setQuery(e.target.value)} /><button onClick={search} className="btn-primary">Search</button></div><div className="grid gap-3">{results.map(r => <article key={r.id} className="timeline-item"><div className="flex items-center justify-between"><b>{r.title}</b><span className="text-xs text-slate-500">score {r.score}</span></div><p className="mt-2 text-sm text-slate-300">{r.snippet}</p></article>)}</div></section>
  </main>;
}
