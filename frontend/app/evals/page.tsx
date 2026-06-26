"use client";

import { useEffect, useState } from "react";
import { API, getJSON, postJSON } from "../lib/api";
import StatusBadge from "../../components/StatusBadge";

type Pack = { id: string; name: string; version: string };
type EvalRun = { id: string; pack_id: string; pack_version: string; summary: any; results: any[]; created_at: string };

export default function EvalLabPage() {
  const [packs, setPacks] = useState<Pack[]>([]);
  const [evals, setEvals] = useState<EvalRun[]>([]);
  const [selectedPack, setSelectedPack] = useState("");
  const [active, setActive] = useState<EvalRun | null>(null);
  const [message, setMessage] = useState("");

  async function load() {
    const [p, e] = await Promise.all([getJSON("/api/packs"), getJSON("/api/evals")]);
    setPacks(p); setEvals(e);
    if (!selectedPack && p[0]) setSelectedPack(p[0].id);
    if (!active && e[0]) setActive(e[0]);
  }
  async function runEval() {
    try {
      const result = await postJSON("/api/evals/run", { pack_id: selectedPack });
      setActive(result); setMessage("Evaluation completed using rule-based checks."); await load();
    } catch (err: any) { setMessage(err.message); }
  }
  useEffect(() => { load().catch(console.error); }, []);

  return <main className="space-y-6">
    <section className="hero-card">
      <p className="eyebrow">Evaluation Lab</p>
      <h1 className="page-title">Regression checks for Agent Packs</h1>
      <p className="page-subtitle">v2 stores evaluation history, computes rule-based failures, validates required tool usage, max steps, policy violations, schema format, and approval expectations.</p>
    </section>

    <section className="card flex flex-col gap-3 lg:flex-row lg:items-end">
      <div className="flex-1"><label className="label">Pack</label><select className="input" value={selectedPack} onChange={e => setSelectedPack(e.target.value)}>{packs.map(p => <option key={p.id} value={p.id}>{p.name} · v{p.version}</option>)}</select></div>
      <button onClick={runEval} className="btn-primary">Run evaluation</button>
      {active && <a href={`${API}/api/evals/${active.id}/report.md`} className="btn-secondary">Export Markdown</a>}
    </section>
    {message && <p className="text-sm text-cyan-300">{message}</p>}

    <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
      <aside className="card space-y-3"><h2 className="section-title">History</h2>{evals.map(e => <button key={e.id} onClick={() => setActive(e)} className={`w-full rounded-xl border p-3 text-left ${active?.id === e.id ? "border-cyan-400 bg-cyan-400/10" : "border-slate-800 bg-slate-950"}`}><div className="font-mono text-xs">{e.id.slice(0,8)}</div><p className="text-xs text-slate-400">v{e.pack_version} · {Math.round((e.summary?.pass_rate || 0)*100)}% pass</p></button>)}</aside>
      <section className="card"><h2 className="section-title mb-4">Results</h2>{active ? <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Case</th><th>Status</th><th>Score</th><th>Failure Reason</th><th>Steps</th><th>Tools Used</th><th>Trace Link</th></tr></thead><tbody>{active.results.map((r, idx) => <tr key={r.case_id || idx}><td>{r.case_id}</td><td><StatusBadge status={r.passed ? "passed" : "failed"} /></td><td>{r.score}</td><td>{(r.failures || []).join("; ") || "—"}</td><td>{r.steps}</td><td>{(r.tools_used || []).join(", ")}</td><td className="text-slate-500">static eval</td></tr>)}</tbody></table></div> : <div className="empty-state">Run or select an evaluation.</div>}</section>
    </div>
  </main>;
}
