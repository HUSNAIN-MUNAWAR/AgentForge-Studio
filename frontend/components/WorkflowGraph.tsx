"use client";
import React from "react";

type Edge = { from?: string; from_?: string; to: string; condition?: string };

function extractListBlock(yamlText: string, key: string): string[] {
  const lines = yamlText.split(/\r?\n/);
  const values: string[] = [];
  let inBlock = false;
  for (const line of lines) {
    if (line.match(new RegExp(`^${key}:\\s*$`))) { inBlock = true; continue; }
    if (inBlock && /^[a-zA-Z_]+:/.test(line)) break;
    if (inBlock) {
      const id = line.match(/id:\s*["']?([a-zA-Z0-9_.-]+)/)?.[1];
      const inline = line.match(/^\s*-\s*["']?([a-zA-Z0-9_.-]+)/)?.[1];
      if (key === "agents" && id) values.push(id);
      if (key !== "agents" && inline && !["from", "to"].includes(inline)) values.push(inline);
    }
  }
  return Array.from(new Set(values));
}

function extractEdges(yamlText: string): Edge[] {
  const edges: Edge[] = [];
  const blocks = yamlText.split(/\n\s*-\s*from:/g);
  for (let i = 1; i < blocks.length; i++) {
    const block = "from:" + blocks[i];
    const from = block.match(/from:\s*["']?([a-zA-Z0-9_.-]+)/)?.[1];
    const to = block.match(/to:\s*["']?([a-zA-Z0-9_.-]+)/)?.[1];
    if (from && to) edges.push({ from, to });
  }
  return edges;
}

export function WorkflowGraph({ yamlText = "", nodes, edges, tools = [], approvals = [] }: { yamlText?: string; nodes?: string[]; edges?: Edge[]; tools?: string[]; approvals?: string[] }) {
  const graphNodes = nodes?.length ? nodes : extractListBlock(yamlText, "agents");
  const graphEdges = edges?.length ? edges : extractEdges(yamlText);
  const graphTools = tools.length ? tools : extractListBlock(yamlText, "tools").filter(t => !t.includes(":"));
  const approvalTools = approvals.length ? approvals : Array.from(yamlText.matchAll(/require_approval:\s*\n([\s\S]*?)(?:\n[a-zA-Z_]+:|$)/g)).flatMap(m => (m[1].match(/-\s*["']?([a-zA-Z0-9_.-]+)/g) || []).map(x => x.replace(/-\s*["']?/, "")));

  return <div>
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <div className="flex min-w-max items-center gap-3">
        <div className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm">User Task</div>
        {(graphNodes.length ? graphNodes : ["start"]).map((n, i) => <React.Fragment key={`${n}-${i}`}>
          <div className="text-slate-500">→</div>
          <div className="rounded-xl border border-indigo-500/50 bg-indigo-500/10 px-4 py-3 text-sm font-semibold">{n}</div>
          {i === (graphNodes.length ? graphNodes.length - 1 : 0) && <><div className="text-slate-500">→</div><div className="rounded-xl border border-emerald-500/50 bg-emerald-500/10 px-4 py-3 text-sm">Final Output</div></>}
        </React.Fragment>)}
      </div>
      <div className="mt-6 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl bg-slate-900 p-3 text-xs"><div className="font-semibold text-slate-300">Edges</div>{graphEdges.length ? graphEdges.map((e, idx) => <div key={idx} className="mt-1 text-slate-400">{e.from || e.from_} → {e.to}</div>) : <div className="mt-1 text-slate-500">No explicit edges parsed.</div>}</div>
        <div className="rounded-xl bg-slate-900 p-3 text-xs"><div className="font-semibold text-slate-300">Tools</div>{graphTools.map(t => <span key={t} className="mr-2 mt-2 inline-block rounded-lg bg-slate-800 px-2 py-1 text-slate-300">{t}</span>)}</div>
        <div className="rounded-xl bg-slate-900 p-3 text-xs"><div className="font-semibold text-slate-300">Approval tools</div>{approvalTools.length ? approvalTools.map(t => <div key={t} className="mt-1 text-amber-300">{t}</div>) : <div className="mt-1 text-slate-500">None</div>}</div>
      </div>
    </div>
  </div>;
}

export default WorkflowGraph;
