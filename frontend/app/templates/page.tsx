"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON } from "../lib/api";
import StatusBadge from "../../components/StatusBadge";

type Pack = { id: string; name: string; version: string; description: string; active: boolean; yaml_text?: string };

export default function TemplatesPage() {
  const [packs, setPacks] = useState<Pack[]>([]);
  useEffect(() => { getJSON("/api/packs").then(setPacks).catch(console.error); }, []);
  return <main className="space-y-6">
    <section className="hero-card"><p className="eyebrow">Template Gallery</p><h1 className="page-title">Start from working Agent Packs</h1><p className="page-subtitle">Each template includes YAML, sample input, eval cases, tools, and docs. Use one directly or duplicate and customize it.</p></section>
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{packs.map(pack => <article key={pack.id} className="card flex flex-col gap-4"><div className="flex items-start justify-between"><div><h2 className="section-title">{pack.name}</h2><p className="text-xs text-slate-500">v{pack.version}</p></div><StatusBadge status={pack.active ? "active" : "inactive"} /></div><p className="text-sm text-slate-300">{pack.description}</p><div className="mt-auto flex gap-2"><Link className="btn-primary" href={`/packs/${pack.id}`}>Customize</Link><Link className="btn-secondary" href="/runs">Run template</Link></div></article>)}</section>
  </main>;
}
