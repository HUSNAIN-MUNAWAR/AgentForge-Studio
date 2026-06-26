import { getJSON } from '../lib/api';
import { StatusBadge } from '@/components/StatusBadge';

export default async function Packs() {
  const packs = await getJSON('/api/packs').catch(() => []);
  return <div className="card">
    <div className="mb-4 flex items-center justify-between"><div><h1 className="text-2xl font-bold">Agent Packs</h1><p className="text-sm text-slate-400">Portable YAML definitions with revision history and validation.</p></div><button disabled title="Use API POST /api/packs/import for now" className="btn">Import UI planned</button></div>
    <div className="overflow-hidden rounded-xl border border-slate-800">
      <table className="table"><thead><tr><th>Name</th><th>Version</th><th>Status</th><th>Description</th><th>Action</th></tr></thead><tbody>
        {packs.map((p: any) => <tr key={p.id}><td className="font-medium">{p.name}</td><td>{p.version}</td><td><StatusBadge status={p.active ? 'active' : 'inactive'} /></td><td className="text-slate-400">{p.description}</td><td><a className="text-indigo-300" href={`/packs/${p.id}`}>Open builder</a></td></tr>)}
      </tbody></table>
    </div>
  </div>;
}
