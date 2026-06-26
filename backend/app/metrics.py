from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
except Exception:  # pragma: no cover
    Counter = Gauge = Histogram = None  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"  # type: ignore
    generate_latest = None  # type: ignore


class _NoopMetric:
    def labels(self, *args, **kwargs):
        return self
    def inc(self, *args, **kwargs):
        return None
    def set(self, *args, **kwargs):
        return None
    def observe(self, *args, **kwargs):
        return None


def _counter(name: str, doc: str, labels: list[str] | None = None):
    return Counter(name, doc, labels or []) if Counter else _NoopMetric()


def _gauge(name: str, doc: str, labels: list[str] | None = None):
    return Gauge(name, doc, labels or []) if Gauge else _NoopMetric()


def _hist(name: str, doc: str, labels: list[str] | None = None):
    return Histogram(name, doc, labels or []) if Histogram else _NoopMetric()


runs_total = _counter("agentforge_runs_total", "Total agent runs by status", ["status"])
run_duration = _hist("agentforge_run_duration_seconds", "Agent run duration in seconds", ["status"])
tool_calls_total = _counter("agentforge_tool_calls_total", "Tool calls by tool and status", ["tool", "status"])
policy_decisions_total = _counter("agentforge_policy_decisions_total", "Policy decisions by decision", ["decision"])
approvals_total = _counter("agentforge_approvals_total", "Approval requests by status", ["status"])
evals_total = _counter("agentforge_evals_total", "Evaluation cases by status", ["status"])
queue_length = _gauge("agentforge_queue_length", "Redis queue length", ["queue"])


def render_metrics() -> tuple[bytes, str]:
    if not generate_latest:
        return b"# prometheus_client not installed\n", "text/plain"
    return generate_latest(), CONTENT_TYPE_LATEST
