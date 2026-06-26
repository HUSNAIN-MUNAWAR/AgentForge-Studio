from __future__ import annotations
from dataclasses import dataclass
from backend.app.core.config import get_settings


@dataclass
class EnqueueResult:
    job_id: str | None
    queue_name: str
    mode: str
    enqueued: bool
    error: str | None = None


def get_queue_length() -> int | None:
    settings = get_settings()
    try:
        from redis import Redis
        from rq import Queue
        conn = Redis.from_url(settings.redis_url)
        queue = Queue(settings.queue_name, connection=conn)
        return len(queue)
    except Exception:
        return None


def enqueue_run_job(run_id: str, file_ids: list[str] | None = None, resume: bool = False) -> EnqueueResult:
    settings = get_settings()
    if settings.queue_execution_mode == "sync" or settings.app_mode == "test":
        return EnqueueResult(job_id=None, queue_name=settings.queue_name, mode="sync", enqueued=False)
    try:
        from redis import Redis
        from rq import Queue, Retry
        conn = Redis.from_url(settings.redis_url)
        queue = Queue(settings.queue_name, connection=conn)
        job = queue.enqueue(
            "backend.app.workers.jobs.execute_run_job",
            run_id,
            file_ids or [],
            resume,
            job_timeout=900,
            retry=Retry(max=2, interval=[10, 30]),
            result_ttl=86400,
            failure_ttl=86400,
        )
        return EnqueueResult(job_id=job.id, queue_name=settings.queue_name, mode="redis", enqueued=True)
    except Exception as exc:
        return EnqueueResult(job_id=None, queue_name=settings.queue_name, mode="fallback", enqueued=False, error=str(exc))
