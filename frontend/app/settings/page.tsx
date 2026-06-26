"use client";

import { useEffect, useState } from "react";
import { getJSON, putJSON } from "../lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [form, setForm] = useState<any>({});
  const [message, setMessage] = useState("");
  async function load() { const s = await getJSON("/api/settings"); setSettings(s); setForm(s); }
  async function save() { const s = await putJSON("/api/settings", form); setSettings(s); setForm(s); setMessage("Runtime settings saved. API keys stay backend-only in .env."); }
  useEffect(() => { load().catch(e => setMessage(e.message)); }, []);
  if (!settings) return <main className="empty-state">Loading settings...</main>;
  return <main className="space-y-6">
    <section className="hero-card"><p className="eyebrow">Settings</p><h1 className="page-title">LLM provider and execution limits</h1><p className="page-subtitle">Configure non-secret runtime settings. Provider API keys are never exposed to the frontend.</p></section>
    {message && <p className="text-sm text-cyan-300">{message}</p>}
    <section className="card grid gap-4 lg:grid-cols-2">
      <div><label className="label">Provider type</label><select className="input" value={form.provider_type || "mock"} onChange={e => setForm({...form, provider_type: e.target.value})}><option value="mock">mock/demo</option><option value="openai_compatible">OpenAI-compatible</option><option value="ollama">Ollama local</option></select></div>
      <div><label className="label">Model name</label><input className="input" value={form.model_name || ""} onChange={e => setForm({...form, model_name: e.target.value})} /></div>
      <div><label className="label">Base URL</label><input className="input" value={form.base_url || ""} onChange={e => setForm({...form, base_url: e.target.value})} /></div>
      <div><label className="label">Temperature</label><input className="input" type="number" step="0.1" value={form.temperature ?? 0.2} onChange={e => setForm({...form, temperature: Number(e.target.value)})} /></div>
      <div><label className="label">Max tokens</label><input className="input" type="number" value={form.max_tokens ?? 1200} onChange={e => setForm({...form, max_tokens: Number(e.target.value)})} /></div>
      <div><label className="label">Max steps per run</label><input className="input" type="number" value={form.max_steps_per_run ?? 32} onChange={e => setForm({...form, max_steps_per_run: Number(e.target.value)})} /></div>
      <div><label className="label">Max cost per run USD</label><input className="input" type="number" step="0.01" value={form.max_cost_per_run_usd ?? 1} onChange={e => setForm({...form, max_cost_per_run_usd: Number(e.target.value)})} /></div>
      <div className="flex items-end"><button onClick={save} className="btn-primary">Save settings</button></div>
    </section>
    <section className="card"><h2 className="section-title">Security note</h2><p className="muted">The UI stores only non-secret settings. Put API keys in backend environment variables such as OPENAI_API_KEY. Local no-auth mode is for trusted development machines.</p></section>
  </main>;
}
