"use client";

import { useEffect, useState } from "react";
import { getJSON, putJSON } from "../lib/api";
import StatusBadge from "../../components/StatusBadge";

type Tool = { name: string; description: string; enabled: boolean; risk_level: string; permission_status: string; config: any };

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [message, setMessage] = useState("");
  async function load() { setTools(await getJSON("/api/tools")); }
  async function update(tool: Tool, patch: Partial<Tool>) {
    await putJSON(`/api/tools/${tool.name}/permissions`, patch);
    setMessage(`Updated ${tool.name}. New runs will use this permission.`);
    await load();
  }
  useEffect(() => { load().catch(e => setMessage(e.message)); }, []);
  return <main className="space-y-6">
    <section className="hero-card"><p className="eyebrow">Tool Runtime</p><h1 className="page-title">Permissions and risk controls</h1><p className="page-subtitle">Every tool has an explicit risk level and permission state. Disabled or blocked tools are enforced by the backend policy layer.</p></section>
    {message && <p className="text-sm text-cyan-300">{message}</p>}
    <section className="card overflow-x-auto"><table className="data-table"><thead><tr><th>Tool</th><th>Description</th><th>Risk</th><th>Enabled</th><th>Permission</th><th>Actions</th></tr></thead><tbody>{tools.map(tool => <tr key={tool.name}><td className="font-mono text-xs">{tool.name}</td><td>{tool.description}</td><td><StatusBadge status={tool.risk_level} /></td><td>{tool.enabled ? "yes" : "no"}</td><td>{tool.permission_status}</td><td><div className="flex flex-wrap gap-2"><button onClick={() => update(tool, { enabled: !tool.enabled })} className="btn-secondary">{tool.enabled ? "Disable" : "Enable"}</button><button onClick={() => update(tool, { permission_status: "allow" })} className="link-button">Allow</button><button onClick={() => update(tool, { permission_status: "approval" })} className="link-button">Approval</button><button onClick={() => update(tool, { permission_status: "block" })} className="link-button text-red-300">Block</button></div></td></tr>)}</tbody></table></section>
  </main>;
}
