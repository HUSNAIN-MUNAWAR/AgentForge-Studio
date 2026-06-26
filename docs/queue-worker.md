# Queue and Worker Architecture

AgentForge Studio v2 includes a real RQ/Redis execution path. The API creates a `Run` row with `queued` status and attempts to enqueue `backend.app.workers.jobs.execute_run_job`. The worker service starts `worker.py`, connects to Redis, and consumes jobs from the configured queue.

If RQ/Redis is unavailable or `QUEUE_EXECUTION_MODE=sync`, the backend executes the run synchronously as a local fallback. This keeps tests and local development deterministic, but Docker Compose uses the worker path by default.

Run metadata stores `job_id`, `queue_name`, `queued_at`, `started_at`, `finished_at`, retry count, status, error message, cost estimate, and latency.
