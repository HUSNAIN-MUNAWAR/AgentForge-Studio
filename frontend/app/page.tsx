export const dynamic = "force-dynamic";
import { getJSON } from './lib/api';
import { MetricCard } from '@/components/MetricCard';
import { StatusBadge } from '@/components/StatusBadge';

export default async function Dashboard() {
  const [packs, runs, approvals, evals, ready] = await Promise.all([
    getJSON('/api/packs').catch(() => []),
    getJSON('/api/runs').catch(() => []),
    getJSON('/api/approvals').catch(() => []),
    getJSON('/api/evals').catch(() => []),
    getJSON('/ready').catch(() => ({}))
  ]);
  const failed = runs.filter((r: any) => r.status === 'failed').length;
  const pending = approvals.filter((a: any) => a.status === 'pending').length;
  const latestEval = evals[0]?.summary?.pass_rate;
  const queued = runs.filter((r: any) => r.status === 'queued').length;
  return <div className="space-y-6">
    <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
      <MetricCard label="Total Packs" value={packs.length} />
      <MetricCard label="Recent Runs" value={runs.length} sub={`${queued} queued`} />
      <MetricCard label="Failed Runs" value={failed} />
      <MetricCard label="Pending Approvals" value={pending} />
      <MetricCard label="Eval Pass Rate" value={latestEval !== undefined ? `${Math.round(latestEval * 100)}%` : '—'} />
      <MetricCard label="Queue Length" value={ready.queue_length ?? '—'} sub={ready.queue_mode || 'unknown'} />
    </div>
    <div className="grid gap-5 xl:grid-cols-3">
      <div className="card xl:col-span-2">
        <div className="mb-4 text-xl font-semibold">Recent runs</div>
        <div className="overflow-hidden rounded-xl border border-slate-800"><table className="table"><thead><tr><th>Run</th><th>Status</th><th>Pack Version</th><th>Latency</th><th>Trace</th></tr></thead><tbody>{runs.slice(0,6).map((r: any) => <tr key={r.id}><td className="font-mono text-xs">{r.id.slice(0,8)}</td><td><StatusBadge status={r.status}/></td><td>{r.pack_version}</td><td>{r.latency_ms} ms</td><td><a className="text-indigo-300" href={`/traces?run=${r.id}`}>Open</a></td></tr>)}</tbody></table></div>
      </div>
      <div className="card">
        <div className="text-xl font-semibold">Quick actions</div>
        <div className="mt-4 grid gap-3">
          <a className="btn" href="/templates">Run a template</a>
          <a className="btn-secondary" href="/packs">Edit agent packs</a>
          <a className="btn-secondary" href="/workflow">Open workflow viewer</a>
          <a className="btn-secondary" href="/evals">Open evaluation lab</a>
        </div>
      </div>
    </div>
  </div>;
}
