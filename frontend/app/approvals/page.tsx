"use client";

import { useEffect, useState } from "react";
import { postJSON, getJSON } from "../lib/api";
import StatusBadge from "../../components/StatusBadge";

type Approval = { id: string; run_id: string; agent_id?: string; tool_name: string; requested_action: string; reason: string; tool_input: any; risk_level: string; policy_rule?: string; status: string; created_at: string };

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  async function load() { setItems(await getJSON("/api/approvals")); }
  async function approve(item: Approval, edited = false) {
    const body = edited ? { edited_tool_input: JSON.parse(editing[item.id] || JSON.stringify(item.tool_input || {})) } : {};
    await postJSON(`/api/approvals/${item.id}/approve`, body); setMessage(`Approved ${item.tool_name}; run queued to resume.`); await load();
  }
  async function reject(item: Approval) { await postJSON(`/api/approvals/${item.id}/reject`, {}); setMessage(`Rejected ${item.tool_name}; run stopped.`); await load(); }
  useEffect(() => { load().catch(e => setMessage(e.message)); }, []);

  return <main className="space-y-6">
    <section className="hero-card"><p className="eyebrow">Human Approval Queue</p><h1 className="page-title">Review risky agent actions</h1><p className="page-subtitle">Approval decisions are stored, traced, and used to resume or stop queued workflow execution.</p></section>
    {message && <p className="text-sm text-cyan-300">{message}</p>}
    <section className="grid gap-4 lg:grid-cols-2">
      {items.map(item => <article key={item.id} className="card space-y-4">
        <div className="flex items-center justify-between"><div><h2 className="section-title">{item.requested_action}</h2><p className="font-mono text-xs text-slate-500">run {item.run_id.slice(0,8)} · {item.agent_id || "agent"}</p></div><StatusBadge status={item.status} /></div>
        <div className="grid gap-3 sm:grid-cols-2"><div className="mini-stat"><span>Tool</span><b>{item.tool_name}</b></div><div className="mini-stat"><span>Risk</span><b>{item.risk_level}</b></div><div className="mini-stat"><span>Rule</span><b>{item.policy_rule || "policy"}</b></div><div className="mini-stat"><span>Status</span><b>{item.status}</b></div></div>
        <p className="text-sm text-slate-300">{item.reason}</p>
        <textarea className="code-panel min-h-[180px] w-full" value={editing[item.id] ?? JSON.stringify(item.tool_input, null, 2)} onChange={e => setEditing({...editing, [item.id]: e.target.value})} />
        <div className="flex flex-wrap gap-2"><button disabled={item.status !== "pending"} onClick={() => approve(item)} className="btn-primary disabled:opacity-40">Approve</button><button disabled={item.status !== "pending"} onClick={() => approve(item, true)} className="btn-secondary disabled:opacity-40">Edit and approve</button><button disabled={item.status !== "pending"} onClick={() => reject(item)} className="btn-danger disabled:opacity-40">Reject</button></div>
      </article>)}
    </section>
    {!items.length && <div className="empty-state">No approval requests yet. Runs that hit medium/high-risk policy rules will appear here.</div>}
  </main>;
}
