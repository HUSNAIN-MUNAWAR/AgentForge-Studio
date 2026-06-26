export function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return <div className="card"><div className="text-sm text-slate-400">{label}</div><div className="mt-2 text-3xl font-bold">{value}</div>{sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}</div>;
}
