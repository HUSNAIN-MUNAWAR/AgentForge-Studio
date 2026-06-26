from __future__ import annotations
import logging
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger("agentforge.worker")


def main() -> None:
    settings = get_settings()
    try:
        from redis import Redis
        from rq import Connection, Worker, Queue
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("RQ worker dependencies are missing. Install backend requirements.") from exc

    conn = Redis.from_url(settings.redis_url)
    queue = Queue(settings.queue_name, connection=conn)
    logger.info("starting rq worker", extra={"run_id": "-", "trace_id": "worker", "span_id": settings.queue_name})
    with Connection(conn):
        Worker([queue]).work(with_scheduler=True)


if __name__ == "__main__":
    main()
