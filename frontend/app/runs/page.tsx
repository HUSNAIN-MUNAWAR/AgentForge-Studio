"use client";

import { useEffect, useMemo, useState } from "react";
import { getJSON, postJSON } from "../lib/api";
import StatusBadge from "../../components/StatusBadge";

type Pack = { id: string; name: string; version: string };
type Run = { id: string; pack_id: string; pack_version: string; input_text: string; status: string; final_output?: string; error_message?: string; job_id?: string; queue_name?: string; latency_ms: number; cost_estimate: number };
type Trace = { span_id: string; event_type: string; agent_id?: string; tool_name?: string; policy_decision?: string; output_summary?: string; status: string; latency_ms: number };

export default function RunsPage() {
  const [packs, setPacks] = useState<Pack[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedPack, setSelectedPack] = useState("");
  const [inputText, setInputText] = useState("Analyze the sample input and produce a concise, traceable report.");
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [error, setError] = useState("");

  async function refresh() {
    const [p, r] = await Promise.all([getJSON("/api/packs"), getJSON("/api/runs")]);
    setPacks(p);
    setRuns(r);
    if (!selectedPack && p[0]) setSelectedPack(p[0].id);
    if (!activeRun && r[0]) setActiveRun(r[0]);
  }

  async function startRun() {
    try {
      const run = await postJSON("/api/runs", { pack_id: selectedPack, input_text: inputText, file_ids: [] });
      setActiveRun(run);
      await refresh();
    } catch (err: any) { setError(err.message); }
  }

  async function loadTraces(run?: Run | null) {
    const target = run || activeRun;
    if (!target) return;
    setActiveRun(target);
    const data = await getJSON(`/api/runs/${target.id}/traces`);
    setTraces(data);
  }

  useEffect(() => { refresh().catch(e => setError(e.message)); }, []);
  useEffect(() => {
    const id = setInterval(() => {
      refresh().catch(() => {});
      if (activeRun) loadTraces(activeRun).catch(() => {});
    }, 3000);
    return () => clearInterval(id);
  }, [activeRun?.id]);

  const activePackName = useMemo(() => packs.find(p => p.id === selectedPack)?.name || "Select pack", [packs, selectedPack]);

  return (
    <main className="space-y-6">
      <section className="hero-card">
        <p className="eyebrow">Run Console</p>
        <h1 className="page-title">Queue-backed agent execution</h1>
        <p className="page-subtitle">Runs are created through the API, queued through Redis/RQ when available, executed by the worker, and continuously persisted as trace spans.</p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <section className="card space-y-4">
          <div>
            <label className="label">Agent Pack</label>
            <select value={selectedPack} onChange={(e) => setSelectedPack(e.target.value)} className="input">
              {packs.map(p => <option key={p.id} value={p.id}>{p.name} · v{p.version}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Task input</label>
            <textarea value={inputText} onChange={(e) => setInputText(e.target.value)} className="input min-h-[180px]" />
          </div>
          <button onClick={startRun} disabled={!selectedPack} className="btn-primary w-full">Start queued run</button>
          {error && <p className="text-sm text-red-300">{error}</p>}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-300">Selected: <b>{activePackName}</b></div>
        </section>

        <section className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="section-title">Recent runs</h2>
            <button onClick={() => refresh()} className="btn-secondary">Refresh</button>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Run</th><th>Status</th><th>Pack</th><th>Queue</th><th>Latency</th><th></th></tr></thead>
              <tbody>
                {runs.map(run => <tr key={run.id}>
                  <td className="font-mono text-xs">{run.id.slice(0, 8)}</td>
                  <td><StatusBadge status={run.status} /></td>
                  <td>v{run.pack_version}</td>
                  <td>{run.queue_name || "sync fallback"}</td>
                  <td>{run.latency_ms} ms</td>
                  <td><button onClick={() => loadTraces(run)} className="link-button">Open</button></td>
                </tr>)}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="card">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="section-title">Live trace / final output</h2>
            <p className="muted">Polling every 3 seconds; WebSocket endpoint also exists for live clients.</p>
          </div>
          {activeRun && <StatusBadge status={activeRun.status} />}
        </div>
        {activeRun ? <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            {traces.map(t => <div key={t.span_id} className="timeline-item">
              <div className="flex items-center justify-between"><b>{t.event_type}</b><span className="text-xs text-slate-500">{t.latency_ms} ms</span></div>
              <p className="text-sm text-slate-400">{t.agent_id || t.tool_name || "system"} {t.policy_decision ? `· ${t.policy_decision}` : ""}</p>
              <p className="mt-1 text-sm text-slate-300">{t.output_summary}</p>
            </div>)}
          </div>
          <pre className="code-panel whitespace-pre-wrap">{activeRun.final_output || activeRun.error_message || "Run output appears here after completion."}</pre>
        </div> : <div className="empty-state">Start or select a run to inspect traces.</div>}
      </section>
    </main>
  );
}
