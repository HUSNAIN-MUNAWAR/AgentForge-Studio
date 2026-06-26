"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { getJSON, putJSON } from "../../lib/api";
import WorkflowGraph from "@/components/WorkflowGraph";
import yaml from "js-yaml";

const tabs = ["Overview", "Agents", "Workflow", "Tools", "Memory", "Policies", "Evaluation", "YAML"];

export default function PackDetail() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [pack, setPack] = useState<any>(null);
  const [tab, setTab] = useState("Overview");
  const [yamlText, setYamlText] = useState("");
  const [status, setStatus] = useState("");
  useEffect(() => { if (id) getJSON(`/api/packs/${id}`).then(data => { setPack(data); setYamlText(data.yaml_text || ""); }); }, [id]);
  const parsed: any = useMemo(() => { try { return yaml.load(yamlText || "") as any || {}; } catch { return {}; } }, [yamlText]);
  function updateYamlField(key: string, value: string) { const obj: any = { ...parsed, [key]: value }; setYamlText(yaml.dump(obj, { lineWidth: 120 })); }
  function updateAgent(index: number, key: string, value: string) { const agents = [...(parsed.agents || [])]; agents[index] = { ...agents[index], [key]: value }; setYamlText(yaml.dump({ ...parsed, agents }, { lineWidth: 120 })); }
  async function validate(){ try { const res = await putJSON(`/api/packs/${id}`, { yaml_text: yamlText, increment_version: false, change_notes: "Validation save" }); setPack(res); setStatus("YAML validated and saved without version bump."); } catch(e:any){ setStatus(e.message); } }
  async function save(){ try { const res = await putJSON(`/api/packs/${id}`, { yaml_text: yamlText, increment_version: true, change_notes: "Saved from v2 builder" }); setPack(res); setYamlText(res.yaml_text || yamlText); setStatus(`Saved as v${res.version}`); } catch(e:any){ setStatus(e.message); } }
  if (!pack) return <main className="card">Loading pack...</main>;
  return <main className="space-y-5">
    <section className="hero-card"><div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><p className="eyebrow">Agent Pack Builder</p><h1 className="page-title">{pack.name}</h1><p className="page-subtitle">{pack.description}</p></div><div className="flex flex-wrap gap-2"><span className="badge">v{pack.version}</span><button className="btn-secondary" onClick={validate}>Validate</button><button className="btn-primary" onClick={save}>Save pack version</button></div></div>{status && <div className="mt-3 rounded-xl bg-slate-950 p-3 text-sm text-slate-300">{status}</div>}</section>
    <div className="flex flex-wrap gap-2">{tabs.map(t => <button key={t} className={tab===t ? "btn-primary" : "btn-secondary"} onClick={()=>setTab(t)}>{t}</button>)}</div>
    {tab==="Overview" && <div className="grid gap-5 lg:grid-cols-2"><div className="card"><h2 className="section-title">Editable overview</h2><label className="label mt-4">Name</label><input className="input" value={parsed.name || ""} onChange={e => updateYamlField("name", e.target.value)} /><label className="label mt-4">Description</label><textarea className="input min-h-32" value={parsed.description || ""} onChange={e => updateYamlField("description", e.target.value)} /><label className="label mt-4">Version</label><input className="input" value={parsed.version || ""} onChange={e => updateYamlField("version", e.target.value)} /><p className="mt-4 text-xs text-slate-500">Saving with version increment creates a revision and bumps the patch version.</p></div><div className="card"><WorkflowGraph yamlText={yamlText}/></div></div>}
    {tab==="Agents" && <div className="grid gap-4 xl:grid-cols-2">{(parsed.agents || []).map((a:any, i:number)=><div className="card space-y-3" key={a.id || i}><div className="flex justify-between"><div><div className="section-title">{a.name}</div><div className="text-xs text-slate-500">{a.id}</div></div><span className="badge">{a.output_schema}</span></div><label className="label">Name</label><input className="input" value={a.name || ""} onChange={e => updateAgent(i, "name", e.target.value)} /><label className="label">Role</label><textarea className="input min-h-20" value={a.role || ""} onChange={e => updateAgent(i, "role", e.target.value)} /><label className="label">Goal</label><textarea className="input min-h-20" value={a.goal || ""} onChange={e => updateAgent(i, "goal", e.target.value)} /><div className="flex flex-wrap gap-2">{(a.tools || []).map((t:string)=><span className="rounded-lg bg-slate-950 px-2 py-1 text-xs text-indigo-200" key={t}>{t}</span>)}</div></div>)}</div>}
    {tab==="Workflow" && <div className="card"><WorkflowGraph yamlText={yamlText}/><div className="mt-4 flex gap-2"><button onClick={validate} className="btn-secondary">Validate workflow</button><button disabled className="btn-disabled">Drag/drop editing planned</button></div></div>}
    {tab==="Tools" && <div className="card"><h2 className="section-title">Tools enabled in this pack</h2><div className="mt-4 flex flex-wrap gap-2">{(parsed.tools || []).map((t:string)=><span className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm" key={t}>{t}</span>)}</div></div>}
    {tab==="Memory" && <div className="card"><h2 className="section-title">Memory</h2><pre className="code-panel mt-4 overflow-auto">{JSON.stringify(parsed.memory || {}, null, 2)}</pre><p className="mt-3 text-sm text-slate-400">v2 implements backend keyword search and the memory.search tool. pgvector is planned.</p></div>}
    {tab==="Policies" && <div className="card"><h2 className="section-title">Policies</h2><pre className="code-panel mt-4 overflow-auto">{JSON.stringify(parsed.policies || {}, null, 2)}</pre></div>}
    {tab==="Evaluation" && <div className="card"><h2 className="section-title">Evaluation</h2><pre className="code-panel mt-4 overflow-auto">{JSON.stringify(parsed.evaluation || {}, null, 2)}</pre><a className="btn-primary mt-4 inline-flex" href={`/evals?pack=${id}`}>Open Evaluation Lab</a></div>}
    {tab==="YAML" && <div className="card"><h2 className="section-title mb-3">YAML Editor</h2><textarea className="code-panel min-h-[620px] w-full" value={yamlText} onChange={e=>setYamlText(e.target.value)} /></div>}
  </main>;
}
