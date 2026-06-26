"use client";

import { useEffect, useState } from "react";
import { getJSON } from "../lib/api";
import StatusBadge from "../../components/StatusBadge";

type Run = { id: string; status: string; pack_version: string; input_text: string };
type Trace = { span_id: string; timestamp: string; event_type: string; agent_id?: string; tool_name?: string; policy_decision?: string; risk_level?: string; latency_ms: number; status: string; input_summary?: string; output_summary?: string; tool_input?: any; tool_output?: any; error_message?: string };

export default function TraceViewerPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selected, setSelected] = useState<Run | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);

  async function load() {
    const data = await getJSON("/api/runs");
    setRuns(data);
    if (!selected && data[0]) await openRun(data[0]);
  }
  async function openRun(run: Run) {
    setSelected(run);
    setTraces(await getJSON(`/api/runs/${run.id}/traces`));
  }
  useEffect(() => { load().catch(console.error); }, []);

  return <main className="space-y-6">
    <section className="hero-card">
      <p className="eyebrow">Trace Viewer</p>
      <h1 className="page-title">AgentOps timeline</h1>
      <p className="page-subtitle">Inspect every workflow step, tool call, policy decision, approval request, error, and latency marker.</p>
    </section>

    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      <aside className="card space-y-3">
        <h2 className="section-title">Runs</h2>
        {runs.map(run => <button key={run.id} onClick={() => openRun(run)} className={`w-full rounded-xl border p-3 text-left ${selected?.id === run.id ? "border-cyan-400 bg-cyan-400/10" : "border-slate-800 bg-slate-950"}`}>
          <div className="flex items-center justify-between"><span className="font-mono text-xs">{run.id.slice(0, 8)}</span><StatusBadge status={run.status} /></div>
          <p className="mt-2 line-clamp-2 text-xs text-slate-400">{run.input_text}</p>
        </button>)}
      </aside>

      <section className="card">
        <div className="mb-4 flex items-center justify-between"><h2 className="section-title">Timeline</h2>{selected && <span className="font-mono text-xs text-slate-500">{selected.id}</span>}</div>
        {traces.length ? <div className="space-y-3">
          {traces.map(span => <article key={span.span_id} className="timeline-item">
            <button className="w-full text-left" onClick={() => setExpanded(expanded === span.span_id ? null : span.span_id)}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2"><StatusBadge status={span.status} /><b>{span.event_type}</b><span className="text-xs text-slate-500">{span.agent_id || span.tool_name || "system"}</span></div>
                <div className="text-xs text-slate-500">{span.latency_ms} ms</div>
              </div>
              <p className="mt-2 text-sm text-slate-300">{span.output_summary || span.error_message}</p>
              <p className="mt-1 text-xs text-slate-500">Policy: {span.policy_decision || "—"} · Risk: {span.risk_level || "—"}</p>
            </button>
            {expanded === span.span_id && <pre className="code-panel mt-3 max-h-[420px] overflow-auto whitespace-pre-wrap">{JSON.stringify(span, null, 2)}</pre>}
          </article>)}
        </div> : <div className="empty-state">No trace spans found yet.</div>}
      </section>
    </div>
  </main>;
}
