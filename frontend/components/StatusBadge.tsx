export function StatusBadge({ status }: { status: string }) {
  const value = String(status || "unknown");
  const cls = ["completed", "approved", "active", "passed", "implemented", "allow", "low"].includes(value)
    ? "badge-green"
    : ["failed", "rejected", "blocked", "block", "high"].includes(value)
    ? "badge-red"
    : ["waiting_approval", "queued", "pending", "medium", "approval", "running"].includes(value)
    ? "badge-yellow"
    : "badge";
  return <span className={cls}>{value}</span>;
}

export default StatusBadge;
