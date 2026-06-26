"use client";

import { useEffect, useState } from "react";
import { getJSON, putJSON } from "../lib/api";
import WorkflowGraph from "../../components/WorkflowGraph";
import StatusBadge from "../../components/StatusBadge";

type Pack = { id: string; name: string; version: string; yaml_text: string; active: boolean };

export default function WorkflowPage() {
  const [packs, setPacks] = useState<Pack[]>([]);
  const [selected, setSelected] = useState<Pack | null>(null);
  const [yamlText, setYamlText] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const data = await getJSON("/api/packs");
    setPacks(data);
    if (!selected && data.length) {
      const detail = await getJSON(`/api/packs/${data[0].id}`);
      setSelected(detail);
      setYamlText(detail.yaml_text || "");
    }
  }

  async function choose(id: string) {
    const detail = await getJSON(`/api/packs/${id}`);
    setSelected(detail);
    setYamlText(detail.yaml_text || "");
    setMessage("");
  }

  async function validate() {
    if (!selected) return;
    try {
      await putJSON(`/api/packs/${selected.id}`, { yaml_text: yamlText, increment_version: false, change_notes: "Workflow validation save" });
      const result = await getJSON(`/api/packs/${selected.id}`);
      setSelected(result);
      setMessage("Workflow YAML is valid and saved without version bump.");
    } catch (err: any) {
      setMessage(`Validation failed: ${err.message}`);
    }
  }

  async function saveVersion() {
    if (!selected) return;
    try {
      const result = await putJSON(`/api/packs/${selected.id}`, { yaml_text: yamlText, increment_version: true, change_notes: "Workflow designer update" });
      setSelected(result);
      setMessage(`Saved new pack version ${result.version}.`);
    } catch (err: any) {
      setMessage(`Save failed: ${err.message}`);
    }
  }

  useEffect(() => { load().catch(e => setMessage(e.message)); }, []);

  return (
    <main className="space-y-6">
      <section className="hero-card">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="eyebrow">Workflow Designer</p>
            <h1 className="page-title">Visualize and validate Agent Pack workflows</h1>
            <p className="page-subtitle">v2 ships a real graph viewer and YAML-backed editor. Drag-and-drop editing is intentionally marked as planned until fully implemented.</p>
          </div>
          <StatusBadge status="implemented" />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="card space-y-3">
          <h2 className="section-title">Agent Packs</h2>
          {packs.map(pack => (
            <button key={pack.id} onClick={() => choose(pack.id)} className={`w-full rounded-xl border p-3 text-left transition ${selected?.id === pack.id ? "border-cyan-400 bg-cyan-400/10" : "border-slate-800 bg-slate-950/60 hover:border-slate-600"}`}>
              <div className="font-semibold">{pack.name}</div>
              <div className="text-xs text-slate-400">v{pack.version}</div>
            </button>
          ))}
        </aside>

        <section className="space-y-6">
          <div className="card">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="section-title">Graph View</h2>
                <p className="muted">Rendered directly from the selected pack YAML.</p>
              </div>
              <button disabled className="btn-disabled">Drag/drop editor planned</button>
            </div>
            {selected ? <WorkflowGraph yamlText={yamlText} /> : <div className="empty-state">Select a pack to render its workflow.</div>}
          </div>

          <div className="card">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="section-title">YAML Editor</h2>
                <p className="muted">This is the source of truth for v2 workflow changes.</p>
              </div>
              <div className="flex gap-2">
                <button onClick={validate} className="btn-secondary">Validate workflow</button>
                <button onClick={saveVersion} className="btn-primary">Save pack version</button>
              </div>
            </div>
            <textarea value={yamlText} onChange={(e) => setYamlText(e.target.value)} className="code-panel min-h-[420px] w-full" />
            {message && <p className="mt-3 text-sm text-cyan-300">{message}</p>}
          </div>
        </section>
      </div>
    </main>
  );
}
